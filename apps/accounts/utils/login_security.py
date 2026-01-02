from django.core.cache import cache
from django.utils import timezone

MAX_FAILED_ATTEMPTS = 5  # 最大失败次数 5次， 防爆破
LOCK_TIME = 60 * 15 # 15分钟

def _cache_key(ip, username):
    return f'登录失败：{ip}:{username}'

def is_locked(ip, username):
    data = cache.get(_cache_key(ip, username))

    if not data:
        return False

    return data['count'] >= MAX_FAILED_ATTEMPTS

def increase_fail(ip, username):
    key = _cache_key(ip, username)
    data = cache.get(key)

    now_ts = int(timezone.now().timestamp())

    if not data:
        cache.set(key, {
            'count': 1,
            'first_fail_ts': now_ts
        }, LOCK_TIME)
    else:
        data['count'] += 1
        cache.set(key, data, LOCK_TIME)

def reset_fail(ip, username):
    cache.delete(_cache_key(ip, username))


def remaining_attempts(ip, username):
    data = cache.get(_cache_key(ip, username))
    if not data:
        return MAX_FAILED_ATTEMPTS
    return max(0, MAX_FAILED_ATTEMPTS - data['count'])