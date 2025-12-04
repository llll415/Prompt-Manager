import os
import time
from sqlalchemy import inspect, text  # <--- 1. 这里加了 text
from werkzeug.security import generate_password_hash
from flask_migrate import migrate, upgrade, init, stamp

# 引入你的应用组件
from app import create_app, db
from models import User

# 创建应用上下文
app = create_app()


def ensure_admin_user():
    """
    [幂等性] 检查并创建管理员账户，确保系统初始化后立即可用。
    """
    admin_username = app.config.get('ADMIN_USERNAME', 'admin')

    try:
        user = User.query.filter_by(username=admin_username).first()
    except Exception:
        return

    if not user:
        print(f"👤 [System] 正在创建管理员账户: {admin_username} ...")
        admin_password = app.config.get('ADMIN_PASSWORD', '123456')
        admin = User(username=admin_username, password_hash=generate_password_hash(admin_password))
        db.session.add(admin)
        db.session.commit()
        print("✅ 管理员账户创建成功！")
    else:
        print(f"✅ 管理员账户 '{admin_username}' 已存在。")


def sync_database():
    """
    [核心逻辑] 智能数据库同步工具 (已增强自动修复功能)
    """
    print("=" * 60)
    print("🛠️  Prompt Manager 智能数据库同步工具 (Smart Sync)")
    print("=" * 60)

    with app.app_context():
        # 1. 检查数据库连接与表状态
        try:
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            db_path = str(db.engine.url)
            print(f"📂 数据库目标: {db_path}")
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return

        # 2. 初始化迁移仓库 (如果不存在)
        # 标记是否刚刚执行了初始化，用于后续判断是否需要重置 DB 版本
        is_fresh_migrations = False

        if not os.path.exists('migrations'):
            print("📦 检测到 migrations 文件夹缺失 (可能是 Docker 镜像更新导致)...")
            print("⚙️  正在重新初始化迁移环境...")
            init()
            is_fresh_migrations = True

        # 3. 智能处理版本冲突
        has_version_table = 'alembic_version' in existing_tables

        if has_version_table and is_fresh_migrations:
            print("⚠️  [自动修复] 检测到数据库有历史记录，但迁移文件已丢失。")
            print("🔄 正在重置数据库版本记录，以匹配当前代码...")
            # 强制删除版本表
            with db.engine.connect() as conn:
                conn.execute(text("DROP TABLE alembic_version"))
                conn.commit()
            print("✅ 版本记录已重置。")
            has_version_table = False  # 更新状态

        # 4. 处理“既有表但无版本号”的情况 (Stamping)
        if 'user' in existing_tables and not has_version_table:
            print("🏷️  正在将当前数据库状态标记为基准版本 (Stamping)...")
            # 注意：如果你的 Model 比 数据库 新，后续的 migrate 会自动检测出差异
            stamp()

        # 5. 执行迁移 (生成脚本 -> 应用变更)
        print("🔍 正在扫描模型变动 (Auto Migrate)...")

        # 使用时间戳防止迁移脚本文件名冲突
        migration_message = f"auto_update_{int(time.time())}"

        try:
            # 尝试生成迁移脚本
            # 这一步会对比 models.py 和 数据库 的差异
            # 如果有差异（比如你加了新字段），它会生成新的脚本
            migrate(message=migration_message)
        except Exception as e:
            print(f"ℹ️  生成迁移脚本提示 (通常可忽略): {e}")

        try:
            print("🚀 正在应用数据库变更 (Upgrade)...")
            upgrade()
            print("✅ 数据库结构已同步至最新。")
        except Exception as e:
            print(f"❌ 升级过程中发生错误: {e}")
            print("提示: 如果是'No changes detected'或'alembic_version'相关错误，通常说明已是最新。")

        # 6. 确保种子数据 (管理员)
        ensure_admin_user()

    print("\n🎉 所有操作完成！系统已就绪。")


if __name__ == '__main__':
    try:
        sync_database()
    except KeyboardInterrupt:
        print("\n🚫 操作已取消。")
    except Exception as e:
        print(f"\n❌ 发生未预期的错误: {e}")