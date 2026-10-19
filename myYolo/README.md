# YOLO 图像标注任务管理平台

基于 Django + DRF 的前后端分离标注任务管理系统：管理员上传数据集发布标注任务，标注员在线认领、提交标注成果，管理员在后台审核，系统按工期自动回收超期任务。

## 功能特性

### 用户与认证

- 用户登录 / 退出，登录采用服务端 PIL 绘制的图形验证码（干扰点、干扰线、随机旋转，验证码存入 Session，5 分钟有效）
- 基于 Session 的登录态，接口统一鉴权校验

### 标注员

- **任务列表**：浏览全部标注任务，支持"只看可领取 / 只看已领取"筛选
- **任务领取**：一键认领任务，自动下载任务数据集压缩包
- **任务归还**：不做的任务可归还，归还后同一任务 24 小时内不可再次领取；近 7 天归还次数达到上限（10 次）将被限制领取
- **成果提交**：上传标注结果压缩包，系统自动校验提交归属（仅本人领取的任务可提交）与标注文件数量（txt 数量须与任务图片数一致）
- **审核结果通知**：20 秒轮询刷新"我的审核结果"，新结果自动弹出提示；支持"只看待修改"筛选，待修改任务自动置顶

### 管理员（Django Admin 后台）

- 任务管理：新建 / 编辑任务，上传数据集压缩包后自动统计图片数量
- 工期设定：每个任务可单独设置工期（小时），默认 48 小时
- 提交审核：查看提交压缩包与备注，审核通过 / 打回并填写修改意见，审核人与审核时间自动记录

### 系统机制

- **任务状态机**：`未领取 → 标注中 → 审核中 → 已完成`，打回后回到标注中
- **超期自动回收**：超过工期的"标注中"任务被系统自动释放回待领取，同时计入归还记录并生成"超期回收"通知
- **审核联动**：审核结果由模型层自动联动任务状态，跨表写入包裹在事务中，并带状态守卫防止非法状态覆盖

## 技术栈

| 层次 | 技术 |
|---|---|
| 后端 | Python 3.12、Django 5.2、Django REST Framework |
| 数据库 | MySQL（mysqlclient） |
| 图像处理 | Pillow（图形验证码） |
| 跨域 | django-cors-headers |
| 前端 | Bootstrap 5.3、原生 JavaScript（XHR + AJAX） |
| 认证 | Session + CsrfExemptSessionAuthentication |

## 项目结构

后端（master 分支）：

```
myYolo/
├── manage.py
├── ARLRDBD.TTF              # 验证码字体
├── myYolo/                  # 项目配置（settings.py 不入库）
└── myapp/                   # 业务应用
    ├── models.py            # Task / Commit / Back / UserTask
    ├── views.py             # 任务领取/归还/提交、超期回收、登录等
    ├── serializers.py
    ├── admin.py             # 审核后台
    ├── code.py              # PIL 图形验证码
    └── migrations/
```

前端（web 分支）：

```
html/
├── login.html               # 登录页
├── task_list.html           # 任务列表（领取 / 归还）
├── use_task.html            # 我的审核结果
├── nav.html                 # 公共导航栏（fetch 注入复用）
└── static/
```

## 数据模型

| 模型 | 说明 |
|---|---|
| Task | 任务：标题、详情、图片数量、数据集文件、状态、标注人、工期、截止时间 |
| Commit | 提交：任务、结果压缩包、提交人、审核状态、修改意见、审核人、审核时间 |
| Back | 归还记录：归还人、任务、归还时间（用于 24 小时冷却与周限领统计） |
| UserTask | 审核结果通知：任务、结果类型（不合格 / 已通过 / 超期回收）、意见、接收人、审核人 |

## 快速开始

环境要求：Python 3.12+、MySQL 8+

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 创建本地配置（真实 settings.py 不入库）
#    Windows 用 copy 命令，macOS/Linux 用 cp
copy myYolo\settings.example.py myYolo\settings.py
cp myYolo/settings.example.py myYolo/settings.py

# 3. 建表并创建管理员
python manage.py migrate
python manage.py createsuperuser

# 4. 启动后端
python manage.py runserver 8000

# 5. 启动前端（web 分支，任意静态服务器）
cd html
python -m http.server 8080
```

### settings.py 必改字段

| 字段 | 说明 |
|---|---|
| `SECRET_KEY` | 会话/CSRF 签名密钥，必须换成自己的随机字符串（文件内注释附有生成命令） |
| `DATABASES` | MySQL 连接信息：库名、用户、密码（库需先手动创建，如 `CREATE DATABASE yolo DEFAULT CHARSET utf8mb4;`） |
| `CORS_ALLOWED_ORIGINS` / `CSRF_TRUSTED_ORIGINS` | 前端实际访问地址，默认 `http://localhost:8080`，端口不同需同步修改 |

模板中已标注 `[必改]` / `[按需修改]` 注释，其余保持默认即可跑通开发环境。

访问 `http://localhost:8080/html/login.html` 登录（前后端请统一使用 localhost，保证 Session Cookie 正常写入），管理员通过 `http://localhost:8000/admin/` 发布任务与审核。

## API 一览

| 接口 | 方法 | 说明 |
|---|---|---|
| `/myapp/image/code/` | GET | 获取图形验证码 |
| `/myapp/login/` | POST | 登录（用户名 + 密码 + 验证码） |
| `/myapp/log/out/` | GET | 退出登录 |
| `/myapp/user/info/` | GET | 当前登录用户信息 |
| `/myapp/task/list/` | GET / POST | 任务列表 / 新建任务 |
| `/myapp/task/set/<id>/` | PUT / PATCH | 领取（status=2）/ 归还（status=1）/ 提交进入审核（status=3） |
| `/myapp/commit/list/` | GET / POST | 提交记录列表 / 提交标注成果 |
| `/myapp/user/task/` | GET | 我的审核结果 |
| `/admin/` | — | 管理后台：任务管理、工期设定、提交审核 |
