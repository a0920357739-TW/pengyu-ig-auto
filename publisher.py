#!/usr/bin/env python3
"""朋域科技 Instagram official API publisher.
Safe-by-default: no requests when AUTO_PUBLISH_ENABLED!=true; reserve state
is committed before any remote publish to prevent silent replays.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import sys
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT=Path(__file__).resolve().parent
QUEUE_FILE=ROOT/'queue.json'
STATE_FILE=ROOT/'state.json'
SELECTED_FILE=ROOT/'.selected_post'
API_VERSION=os.environ.get('META_API_VERSION','v26.0')
BASE=f'https://graph.instagram.com/{API_VERSION}'

def log(msg): print('[PENGYU IG] '+msg,flush=True)
def read_json(file):return json.loads(file.read_text(encoding='utf-8'))
def save_state(state):
    tmp=STATE_FILE.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    tmp.replace(STATE_FILE)

def queue():
    q=read_json(QUEUE_FILE)
    for p in q.get('posts',[]):
        assert p['id'] and p['type'] in ('IMAGE','REELS')
        assert len(p['caption'])<=2200, 'Caption over IG 2200 chars'
        assert (ROOT/'docs/media'/p['asset']).is_file(), f'Missing file: {p["asset"]}'
    assert len({p['id'] for p in q.get('posts',[])})==len(q.get('posts',[])),'Duplicate IDs'
    return q

def state():return read_json(STATE_FILE)
def next_post():
    st=state()['entries']
    for p in queue()['posts']:
        if p.get('approved') and p['id'] not in st:return p
    return None

def media_base():
    url=os.environ.get('MEDIA_BASE_URL','').strip().rstrip('/')
    if url:return url
    repo=os.environ.get('GITHUB_REPOSITORY','')
    if '/' not in repo:raise RuntimeError('MEDIA_BASE_URL 或 GITHUB_REPOSITORY 未設定')
    owner,name=repo.split('/',1)
    return f'https://{owner.lower()}.github.io/{name}/media'

def check_media(url,type_):
    if not url.startswith('https://'):raise RuntimeError('素材 URL 必須是公開 HTTPS')
    req=Request(url,method='HEAD',headers={'User-Agent':'PengyuIGPublisher/1.0'})
    try:
        with urlopen(req,timeout=25) as resp:
            mime=resp.headers.get('content-type','').split(';')[0].strip().lower()
            code=resp.status
    except Exception as e: raise RuntimeError('媒體公開網址無法讀取，請確認 GitHub Pages 已上線：'+str(e)) from e
    allowed=('image/jpeg',) if type_=='IMAGE' else ('video/mp4','application/octet-stream')
    if code!=200 or mime not in allowed:
        raise RuntimeError(f'公開素材內容類型錯誤：HTTP {code}, {mime}；應為 {allowed}')

def token_info():
    token=os.environ.get('IG_ACCESS_TOKEN','').strip()
    igid=os.environ.get('IG_USER_ID','').strip()
    if not token or not igid:raise RuntimeError('IG_ACCESS_TOKEN / IG_USER_ID 未在 GitHub Secrets 設定')
    if not igid.isdigit():raise RuntimeError('IG_USER_ID 必須是 Meta 顯示的數字 IG 帳號 ID')
    return token,igid

def graph_call(method,path,token,data=None,params=None):
    url=BASE+path
    if params:url+='?'+urlencode(params)
    payload=None
    if method=='POST':
        payload=urlencode(data or {}).encode('utf-8')
    req=Request(url,method=method,data=payload,headers={
        'Authorization':'Bearer '+token,'Accept':'application/json',
        'Content-Type':'application/x-www-form-urlencoded','User-Agent':'PengyuIGPublisher/1.0'})
    try:
        with urlopen(req,timeout=80) as resp:
            output=resp.read().decode('utf-8')
        return json.loads(output)
    except HTTPError as exc:
        body=exc.read().decode('utf-8',errors='replace')[:1300]
        # Token may occasionally be echoed by bad gateways; suppress it.
        body=body.replace(token,'[REDACTED]')
        raise RuntimeError(f'Meta HTTP {exc.code}: {body}') from None
    except (URLError,TimeoutError) as exc:
        raise RuntimeError(f'Meta 連線失敗（請勿盲目重發，確認帳號後再檢查）：{exc}') from exc

def account_check(token,igid):
    info=graph_call('GET','/me',token,params={'fields':'user_id,username'})
    if str(info.get('user_id') or info.get('id') or '')!=igid:
        raise RuntimeError('IG_USER_ID 與目前 token 所屬帳號不同，已停止，避免發錯帳號')
    log('已驗證官方 Meta 連線，帳號 @'+str(info.get('username','(unknown)')))

def preview():
    q=queue();st=state()['entries'];p=next_post()
    log(f'素材 {len(q["posts"])} 則；已發布 {sum(x.get("status")=="published" for x in st.values())} 則；需人工檢查 {sum(x.get("status") in ("reserved","needs_review") for x in st.values())} 則')
    if p:log(f'下一篇：{p["id"]} | {p["type"]} | {p["title"]} | {p["asset"]}')
    else:log('已沒有待發的核准內容，系統將停止發布；請先補內容')
    return 0

def reserve(force=False):
    if os.environ.get('AUTO_PUBLISH_ENABLED','').lower()!='true':
        log('AUTO_PUBLISH_ENABLED 尚未設為 true，目前禁止真正發文')
        SELECTED_FILE.write_text('',encoding='utf-8')
        return 0
    if not force and dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).weekday() not in (0,2,4):
        log('今天不是台灣時間週一、三、五；略過')
        SELECTED_FILE.write_text('',encoding='utf-8')
        return 0
    p=next_post()
    SELECTED_FILE.write_text('',encoding='utf-8')
    if not p:
        log('貼文清單已發完／尚未核准，略過')
        return 0
    token,igid=token_info()
    account_check(token,igid)
    url=f'{media_base()}/{p["asset"]}'
    check_media(url,p['type'])
    s=state()
    if p['id'] in s['entries']:raise RuntimeError('偵測到已有預約，避免重複發布')
    s['entries'][p['id']]={'status':'reserved','reserved_at':dt.datetime.now(dt.timezone.utc).isoformat()}
    save_state(s)
    SELECTED_FILE.write_text(p['id'],encoding='utf-8')
    log('已預留 '+p['id']+'；請先由 GitHub Actions 將 state.json 提交，再執行發布')
    return 0

def publish():
    if os.environ.get('AUTO_PUBLISH_ENABLED','').lower()!='true':
        log('禁止發布：AUTO_PUBLISH_ENABLED != true')
        return 0
    if not SELECTED_FILE.exists() or not SELECTED_FILE.read_text(encoding='utf-8').strip():
        log('本輪沒有已預留貼文')
        return 0
    postid=SELECTED_FILE.read_text(encoding='utf-8').strip()
    p=next((x for x in queue()['posts'] if x['id']==postid),None)
    s=state()
    ent=s['entries'].get(postid)
    if not p or not ent or ent.get('status')!='reserved':
        raise RuntimeError('保護機制：找不到本輪已保留且核准的貼文')
    token,igid=token_info()
    url=f'{media_base()}/{p["asset"]}'
    try:
        account_check(token,igid)
        params={'caption':p['caption']}
        if p['type']=='REELS':
            params.update({'media_type':'REELS','video_url':url,'share_to_feed':'true'})
        else:
            params.update({'image_url':url})
        container=graph_call('POST',f'/{igid}/media',token,data=params)
        cid=container.get('id')
        if not cid:raise RuntimeError('Meta 未回傳媒體容器 ID')
        # Record creation before publish in memory; final file state is committed by Action.
        ent['container_id']=str(cid)
        ready=False
        for attempt in range(42):
            st=graph_call('GET',f'/{cid}',token,params={'fields':'status_code'})
            status=st.get('status_code','')
            if status=='FINISHED':ready=True;break
            if status in ('ERROR','EXPIRED'):
                raise RuntimeError(f'Meta 媒體轉檔失敗：{status}')
            time.sleep(8 if p['type']=='REELS' else 3)
        if not ready:raise RuntimeError('Meta 處理影片逾時；請先確認 IG 是否已發布再決定是否重試')
        log('媒體容器就緒，正式發布 '+p['id'])
        result=graph_call('POST',f'/{igid}/media_publish',token,data={'creation_id':cid})
        media_id=str(result.get('id',''))
        if not media_id:raise RuntimeError('Meta 未回傳貼文 ID；請檢查帳號是否實際已發文')
        ent.update({'status':'published','media_id':media_id,'published_at':dt.datetime.now(dt.timezone.utc).isoformat()})
        save_state(s)
        log(f'成功發布 {p["id"]}；媒體 ID：{media_id}')
        return 0
    except Exception as e:
        # No automatic retry; if publish timed out, the server might have posted.
        ent.update({'status':'needs_review','error':str(e)[:400]})
        save_state(s)
        log('需要人工確認：'+str(e))
        return 1

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--phase',choices=['preview','reserve','publish'],default='preview')
    ap.add_argument('--force',action='store_true')
    args=ap.parse_args()
    try:
        if args.phase=='preview':return preview()
        if args.phase=='reserve':return reserve(force=args.force)
        if args.phase=='publish':return publish()
    except Exception as e:
        log('安全停止：'+str(e));return 1
    return 1

if __name__=='__main__':sys.exit(main())
