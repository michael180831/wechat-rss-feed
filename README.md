# WeChat Public Account Monitor

微信公众号更新监控工具，自动检测更新并发送通知。

## 功能
- 自动检测配置的公众号更新状态
- 发现更新时创建GitHub Issue记录
- 通过邮件及时通知更新信息

## 配置说明

### 环境变量
在GitHub仓库的Secrets中配置以下变量：
- `EMAIL_ADDRESS`: 通知邮件地址
- `EMAIL_PASSWORD`: 邮箱密码
- `SMTP_SERVER`: SMTP服务器地址
- `SMTP_PORT`: SMTP服务器端口

### 监控配置
在 `biz.txt` 文件中添加需要监控的公众号biz值（Base64格式），每行一个。

## 工作流程
1. 通过GitHub Actions每小时自动检查一次更新
2. 发现更新时：
   - 自动创建Issue记录更新信息
   - 发送邮件通知
3. 收到通知后手动查看对应公众号内容

## 维护说明
- 添加新公众号：在 `biz.txt` 中添加对应的base64编码的biz值
- 删除监控：从 `biz.txt` 中删除对应行
