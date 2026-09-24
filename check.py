# check.py
import os
import datetime
import requests

TOKEN = os.environ["DORM_TOKEN"]
THRESHOLD = float(os.environ.get("THRESHOLD", "40"))
GH_TOKEN = os.environ["GITHUB_TOKEN"]
REPO = os.environ["GITHUB_REPOSITORY"]
OWNER = REPO.split("/")[0]

IMPL_TYPE     = os.environ["IMPL_TYPE"]
SCHOOL_AREA   = os.environ["SCHOOL_AREA_NO"]
BUILDING_NO   = os.environ["BUILDING_NO"]
ROOM_NUM      = os.environ["ROOM_NUM"]

ISSUE_TITLE = f"⚠️ 宿舍电量低于 {THRESHOLD:g} 度"
URL = "https://user.fosu.edu.cn/powerfee/getBalance"

gh_headers = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
}

def list_open_issues():
    r = requests.get(
        f"https://api.github.com/repos/{REPO}/issues",
        headers=gh_headers,
        params={"state": "open", "per_page": 100},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()

def bj_now():
    tz = datetime.timezone(datetime.timedelta(hours=8))
    return datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M")

# ---------- 1. 查询电量 ----------
data = {
    "implType":     IMPL_TYPE,
    "schoolAreaNo": SCHOOL_AREA,
    "buildingNo":   BUILDING_NO,
    "roomNum":      ROOM_NUM,
    "from":         "wxminiprogram",
    "token":        TOKEN,
}

r = requests.post(URL, data=data, timeout=15)
r.raise_for_status()
j = r.json()
if not j.get("ret"):
    raise SystemExit(f"接口失败: {j.get('msg')}")

balance = float(j["obj"]["powerBalance"])
room = j["obj"].get("room", "未知")
print(f"[{room}] 当前电量: {balance} 度，阈值 {THRESHOLD}")

# ---------- 2. 拿到 open issue ----------
issues = list_open_issues()
existing = [i for i in issues if i.get("title") == ISSUE_TITLE]

# ---------- 3. 分支处理 ----------
if balance < THRESHOLD:
    if existing:
        issue_number = existing[0]["number"]
        resp = requests.post(
            f"https://api.github.com/repos/{REPO}/issues/{issue_number}/comments",
            headers=gh_headers,
            json={
                "body": (
                    f"⏰ **{bj_now()}** 电量为 **{balance:.2f} 度**，"
                    f"仍低于阈值 {THRESHOLD:g} 度，请及时充值。"
                )
            },
            timeout=15,
        )
        resp.raise_for_status()
        print(f"已在 Issue #{issue_number} 追加提醒")
    else:
        resp = requests.post(
            f"https://api.github.com/repos/{REPO}/issues",
            headers=gh_headers,
            json={
                "title": ISSUE_TITLE,
                "body": (
                    f"**{room}** 当前剩余 **{balance:.2f} 度**，"
                    f"低于阈值 {THRESHOLD:g} 度，请及时充值。\n\n"
                    f"> 由 GitHub Actions 自动创建，电量恢复后将自动关闭。"
                ),
                "assignees": [OWNER],
            },
            timeout=15,
        )
        resp.raise_for_status()
        print(f"创建 Issue: {resp.json().get('html_url')}")
else:
    if not existing:
        print("电量充足，且无未关闭预警，无需操作")
    else:
        for i in existing:
            resp = requests.patch(
                f"https://api.github.com/repos/{REPO}/issues/{i['number']}",
                headers=gh_headers,
                json={
                    "state": "closed",
                    "state_reason": "completed",
                    "body": (
                        f"电量已恢复至 **{balance:.2f} 度**，"
                        f"高于阈值 {THRESHOLD:g} 度，自动关闭。"
                    ),
                },
                timeout=15,
            )
            resp.raise_for_status()
            print(f"已自动关闭 Issue #{i['number']}")