# 故障排查

## 1. 缺少配置

现象：脚本启动即失败。

重点检查：
- `wechat_appid`
- `wechat_secret`
- `default_thumb_media_id`（若未显式传入，且正文没有可自动做封面的图片）

---

## 2. 缺少可用封面

常见现象：
- 微信返回 `errcode=40007`
- 没有 `--cover-image`
- 也没有 `default_thumb_media_id`
- 正文里没有本地图片，或图片路径解析失败

处理：
1. 最稳：显式传入 `--cover-image`
2. 或显式传入 `--thumb-media-id`
3. 或在配置中设置 `default_thumb_media_id`
4. 或确保正文里至少有一张本地可访问图片，供自动取首图封面

---

## 3. 微信 IP 白名单问题

常见错误：`40164`

说明：服务器出口 IP 不在公众号后台白名单中。

处理：
1. 查看当前服务器出口 IP
2. 登录微信公众号后台
3. 将出口 IP 加入白名单
4. 等几分钟后重试

---

## 4. 封面素材过期

现象：`thumb_media_id` 无效或过期。

处理：
1. 重新上传封面图
2. 更新 `default_thumb_media_id`
3. 或在本次调用里显式传入新的 `--thumb-media-id`

---

## 5. 微信 token 获取失败

重点检查：
- AppID / Secret 是否正确
- 公众号类型是否支持相关接口
- 服务器是否能访问 `api.weixin.qq.com`

---

## 6. 正文图片显示异常 / 插图未生效

现象：
- 图片没显示
- `image_report.unresolved_sources` 非空

处理：
1. 先检查图片路径是否相对文章文件本身可解析
2. 再检查图片文件是否真实存在
3. 公网 URL 图片可直接保留
4. 本地图片推荐使用相对文章文件的稳定路径
5. 如果用的是新增插图参数，检查 `--body-image`、`--body-image-placement`、`--max-body-images`
6. 先用 `--check` 看 `inserted_body_images` 是否符合预期

---

## 7. 配图状态卡住（blocked-by-image）

现象：
- 返回错误：`当前配图状态为 blocked-by-image，按门禁不继续推进草稿箱`

处理：
1. 先修复专属配图，再用 `--image-state article-specific` 重试
2. 或明确降级：`--image-state text-only` / `fallback-approved`

---

## 8. 建议的最稳调试顺序

1. 先跑 `--check`
2. 看 `cover_strategy` + `image_state`
3. 再看 `body_image_count` + `inserted_body_images`
4. 真发失败时，再看 `image_report` 和 `next_action`
