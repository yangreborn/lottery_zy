# 里程碑5 微信登录排查 设计（note 33）

**目标：** 回答「微信登录失败是不是没配置」——是。并让后端在未配置时返回**明确的诊断错误**，而非笼统「微信登录失败」，便于自查。

## 结论（note 33 的答案）

微信登录走 `WechatLoginView` → `wechat_code_to_openid`，需要：
1. 后端配置 `WECHAT_APPID` + `WECHAT_SECRET`（`config/settings.py:133-134` 读环境变量，默认空字符串）。这两项是密钥类信息，应放环境变量/部署密钥，不写进代码仓库。
2. 前端在**真实微信小程序**里运行（`uni.login` 才能拿到有效 `code`；H5/开发者工具非微信环境拿不到，会走 `fail` 提示「请在微信小程序中使用」）。

当前未配置 AppID/Secret，所以失败属预期。

## 方案（小改进：明确的未配置提示）

`WechatLoginView.post` 在调用 `wechat_code_to_openid` 之前先校验配置：

```python
from django.conf import settings
...
        if not settings.WECHAT_APPID or not settings.WECHAT_SECRET:
            return Response(make_response(code=1, msg="微信登录未配置",
                                          error="后端缺少 WECHAT_APPID/WECHAT_SECRET"))
```

这样开发态调用 `/api/user/login/wechat` 会得到「微信登录未配置」，一眼可知是配置缺失而非 code 问题。配置齐全后才进入真实 code2session 流程（失败仍返回原「微信登录失败」）。

匿名登录（`LoginView`）不受影响，始终可用。

## 文件

- 修改：`lottery_backend/usernumber/views.py`（WechatLoginView 增配置校验）
- 测试：`lottery_backend/usernumber/tests/test_token_auth.py`（或新增微信登录测试文件）

## 测试

- 未配置（settings.WECHAT_APPID 空）时 POST `/api/user/login/wechat` 返回 `code=1`、`msg="微信登录未配置"`。
- 配置齐全但 code 无效时（monkeypatch `wechat_code_to_openid` 返回 None）返回 `code=1`、`msg="微信登录失败"`（原行为保留）。
