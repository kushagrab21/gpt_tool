import requests, json


def call_api(task, data=None, settings=None):
    payload = {
        "task": task,
        "data": data or {},
        "settings": settings or {}
    }
    from .config import BASE_URL
    res = requests.post(BASE_URL, json=payload)
    try:
        return res.json()
    except:
        return {"raw": res.text}

