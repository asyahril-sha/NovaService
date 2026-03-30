# main.py
"""
NovaService - Main Entry Point
Virtual Service Provider dengan 16 karakter
"""

import os
import sys
import asyncio
import signal
import logging
import time
from pathlib import Path
from datetime import datetime

from aiohttp import web
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from telegram.request import HTTPXRequest

from config import get_settings
from commands import register_general_commands, register_role_commands
from handlers.message import message_handler, set_nova_available
from commands.role import cmd_status

__version__ = "1.0.0"

# =============================================================================
# SETUP LOGGING
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-5s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True
)
logger = logging.getLogger("NOVASERVICE")

# =============================================================================
# GLOBAL VARIABLES
# =============================================================================
_application = None
_backup_dir = Path("data/backups")
_backup_dir.mkdir(parents=True, exist_ok=True)

# Flag untuk Nova availability
NOVA_AVAILABLE = True
set_nova_available(NOVA_AVAILABLE)


# =============================================================================
# COMMAND HANDLERS
# =============================================================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /start"""
    user_id = update.effective_user.id
    settings = get_settings()
    
    if user_id != settings.admin_id:
        await update.message.reply_text("❌ Maaf, Anda tidak memiliki akses ke bot ini.")
        return
    
    # Cek apakah ada sesi aktif
    from utils.user_mode import get_active_role, get_user_flow
    active_role = await get_active_role(user_id)
    flow = await get_user_flow(user_id)
    
    if active_role and flow and flow.is_active:
        await update.message.reply_text(
            f"💜 *Sesi {active_role} masih berjalan!*\n\n"
            f"Ketik /status untuk lihat status\n"
            f"Ketik /batal untuk mengakhiri sesi\n"
            f"Ketik /pause untuk jeda sejenak\n"
            f"Ketik /resume untuk melanjutkan",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text(
        "💜 *NOVASERVICE* 💜\n\n"
        "Selamat datang, Mas.\n\n"
        "Command yang tersedia:\n"
        "• /nova - Panggil Nova\n"
        "• /role therapist - Panggil therapist\n"
        "• /role pelacur - Panggil pelacur\n"
        "• /status - Lihat status sesi\n"
        "• /pause - Jeda sesi sementara\n"
        "• /resume - Lanjutkan sesi\n"
        "• /batal - Kembali ke mode chat\n\n"
        "Nikmati, Mas. 💜",
        parse_mode='Markdown'
    )


async def cmd_nova(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /nova"""
    user_id = update.effective_user.id
    settings = get_settings()
    
    if user_id != settings.admin_id:
        await update.message.reply_text("❌ Maaf, Anda tidak memiliki akses ke bot ini.")
        return
    
    # Cek apakah ada sesi aktif
    from utils.user_mode import get_active_role, get_user_flow
    active_role = await get_active_role(user_id)
    flow = await get_user_flow(user_id)
    
    if active_role and flow and flow.is_active:
        await update.message.reply_text(
            f"💜 *Sesi {active_role} masih berjalan!*\n\n"
            f"Ketik /status untuk lihat status\n"
            f"Ketik /batal untuk mengakhiri sesi",
            parse_mode='Markdown'
        )
        return
    
    # Reset ke mode chat
    from utils.user_mode import set_user_mode
    await set_user_mode(user_id, 'chat')
    
    await update.message.reply_text(
        "*Nova tersenyum*\n\n\"Iya, Mas. Ada yang bisa Nova bantu?\"\n\n"
        "Ketik /role therapist atau /role pelacur untuk memulai service.",
        parse_mode='Markdown'
    )


async def cmd_batal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /batal - Batalkan sesi dan kembali ke Nova"""
    user_id = update.effective_user.id
    settings = get_settings()
    
    if user_id != settings.admin_id:
        await update.message.reply_text("❌ Maaf, command hanya untuk admin.")
        return
    
    from utils.user_mode import get_active_role, get_user_flow, set_user_mode
    from handlers.message import _stop_auto_send
    
    active_role = await get_active_role(user_id)
    flow = await get_user_flow(user_id)
    
    if active_role and flow:
        # Hentikan auto-send
        await _stop_auto_send(user_id)
        
        # Hentikan flow
        if hasattr(flow, 'is_active'):
            flow.is_active = False
        if hasattr(flow, 'auto_send_active'):
            flow.auto_send_active = False
        if hasattr(flow, 'auto_send_running'):
            flow.auto_send_running = False
    
    # Reset ke mode chat
    await set_user_mode(user_id, 'chat')
    
    await update.message.reply_text(
        "💜 *KEMBALI KE NOVA* 💜\n\n"
        "Nova di sini, Mas. Ada yang bisa dibantu?",
        parse_mode='Markdown'
    )


async def cmd_pause(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /pause - Jeda sesi sementara"""
    user_id = update.effective_user.id
    settings = get_settings()
    
    if user_id != settings.admin_id:
        await update.message.reply_text("❌ Maaf, command hanya untuk admin.")
        return
    
    from utils.user_mode import get_active_role, get_user_flow
    
    active_role = await get_active_role(user_id)
    flow = await get_user_flow(user_id)
    
    if not active_role or not flow:
        await update.message.reply_text("📭 Tidak ada sesi yang sedang berjalan.")
        return
    
    if not flow.is_active:
        await update.message.reply_text("📭 Sesi tidak aktif.")
        return
    
    if hasattr(flow, 'is_paused') and flow.is_paused:
        await update.message.reply_text("⏸️ Sesi sudah dalam keadaan pause.")
        return
    
    # Pause session
    if hasattr(flow, 'pause'):
        await flow.pause()
        await update.message.reply_text(
            "⏸️ *Sesi di-pause*\n\n"
            "Ketik /resume untuk melanjutkan sesi.\n"
            "Ketik /batal untuk mengakhiri sesi.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Fitur pause tidak tersedia untuk role ini.")


async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /resume - Lanjutkan sesi yang di-pause"""
    user_id = update.effective_user.id
    settings = get_settings()
    
    if user_id != settings.admin_id:
        await update.message.reply_text("❌ Maaf, command hanya untuk admin.")
        return
    
    from utils.user_mode import get_active_role, get_user_flow
    
    active_role = await get_active_role(user_id)
    flow = get_user_flow(user_id)
    
    if not active_role or not flow:
        await update.message.reply_text("📭 Tidak ada sesi yang sedang berjalan.")
        return
    
    if not hasattr(flow, 'is_paused') or not flow.is_paused:
        await update.message.reply_text("▶️ Tidak ada sesi yang di-pause.")
        return
    
    # Resume session
    if hasattr(flow, 'resume'):
        await flow.resume()
        await update.message.reply_text(
            "▶️ *Sesi dilanjutkan*\n\n"
            "Role akan melanjutkan aktivitas.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Fitur resume tidak tersedia untuk role ini.")


# =============================================================================
# WEBHOOK HANDLERS
# =============================================================================

async def webhook_handler(request):
    """Handle Telegram webhook"""
    global _application
    
    logger.info(f"📨 Webhook called: {request.method} {request.path}")
    
    if request.method == 'GET':
        return web.Response(
            text="This endpoint is for Telegram webhook. Use POST method.",
            status=405
        )
    
    if not _application:
        logger.error("❌ _application is None! Bot not ready")
        return web.Response(status=503, text='Bot not ready')
    
    try:
        update_data = await request.json()
        logger.info(f"📨 Received update: {update_data}")
        
        if not update_data:
            return web.Response(status=400, text='No data')
        
        update = Update.de_json(update_data, _application.bot)
        await _application.process_update(update)
        logger.info("✅ Update processed successfully")
        return web.Response(text='OK', status=200)
        
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return web.Response(status=500, text='Error')


async def health_handler(request):
    """Health check endpoint"""
    return web.json_response({
        "status": "healthy",
        "bot": "NovaService",
        "version": __version__,
        "nova_available": NOVA_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    })


async def root_handler(request):
    """Root endpoint"""
    return web.json_response({
        "name": "NovaService",
        "version": __version__,
        "status": "running",
        "characters": {
            "therapist": 8,
            "pelacur": 8,
            "total": 16
        }
    })


# =============================================================================
# MAIN BOT CLASS
# =============================================================================

class NovaServiceBot:
    def __init__(self):
        self.start_time = time.time()
        self.application: Application = None
        self._shutdown_flag = False
        self._runner = None
    
    async def init_nova(self) -> bool:
        global NOVA_AVAILABLE
        logger.info("💜 Initializing NovaService...")
        try:
            from memory.persistent import get_nova_persistent
            persistent = await get_nova_persistent()
            
            logger.info("✅ NovaService ready!")
            logger.info(f"   Characters: 16 (8 Therapist, 8 Pelacur)")
            logger.info(f"   Service: Therapist (3 jam) | Pelacur (10 jam)")
            
            NOVA_AVAILABLE = True
            set_nova_available(True)
            return True
        except Exception as e:
            logger.error(f"NovaService init error: {e}", exc_info=True)
            NOVA_AVAILABLE = False
            set_nova_available(False)
            return False
    
    async def init_application(self) -> Application:
        settings = get_settings()
        logger.info("🔧 Initializing Telegram application...")
        request = HTTPXRequest(connection_pool_size=50, connect_timeout=60)
        app = ApplicationBuilder().token(settings.telegram_token).request(request).build()
        
        # ========== REGISTER ALL COMMANDS ==========
        # General commands
        app.add_handler(CommandHandler("start", cmd_start))
        app.add_handler(CommandHandler("nova", cmd_nova))
        app.add_handler(CommandHandler("batal", cmd_batal))
        app.add_handler(CommandHandler("pause", cmd_pause))
        app.add_handler(CommandHandler("resume", cmd_resume))
        app.add_handler(CommandHandler("status", cmd_status))
        
        # Role commands (dari register_role_commands)
        register_role_commands(app)
        
        # Message handler (must be last)
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
        
        # Error handler
        async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            logger.error(f"Error: {context.error}", exc_info=True)
            try:
                if update and update.effective_message:
                    await update.effective_message.reply_text(
                        "❌ Terjadi error internal. Silakan coba lagi nanti, Mas.",
                        parse_mode='Markdown'
                    )
            except Exception:
                pass
        
        app.add_error_handler(error_handler)
        
        handler_count = sum(len(h) for h in app.handlers.values())
        logger.info(f"✅ Handlers registered: {handler_count}")
        return app
    
    async def setup_webhook(self) -> bool:
        settings = get_settings()
        railway_url = settings.webhook.railway_domain or settings.webhook.railway_static_url
        
        if not railway_url:
            logger.info("🌐 No webhook URL (Railway domain not set), using polling mode")
            return False
        
        webhook_url = f"https://{railway_url}{settings.webhook.path}"
        logger.info(f"🔗 Setting webhook to: {webhook_url}")
        
        try:
            await self.application.bot.delete_webhook(drop_pending_updates=True)
            await self.application.bot.set_webhook(
                url=webhook_url,
                allowed_updates=['message', 'callback_query'],
                drop_pending_updates=True
            )
            
            info = await self.application.bot.get_webhook_info()
            logger.info(f"📡 Webhook info: {info.url}")
            
            if info.url == webhook_url:
                logger.info("✅ Webhook verified!")
                return True
            else:
                logger.warning(f"⚠️ Webhook URL mismatch: set={webhook_url}, actual={info.url}")
                return False
            
        except Exception as e:
            logger.error(f"Webhook setup error: {e}", exc_info=True)
            return False
    
    async def start_web_server(self):
        settings = get_settings()
        port = int(os.environ.get("PORT", 8080))
        
        app = web.Application()
        app.router.add_get('/', root_handler)
        app.router.add_get('/health', health_handler)
        app.router.add_post(settings.webhook.path, webhook_handler)
        
        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, '0.0.0.0', port)
        await site.start()
        logger.info(f"🌐 Web server running on port {port}")
        logger.info(f"   Health check: http://localhost:{port}/health")
        logger.info(f"   Webhook endpoint: POST http://localhost:{port}{settings.webhook.path}")
        if settings.webhook.railway_domain:
            logger.info(f"   Public URL: https://{settings.webhook.railway_domain}{settings.webhook.path}")
    
    async def start(self):
        """Start bot"""
        global _application
        
        logger.info("=" * 70)
        logger.info(f"🚀 NovaService v{__version__} Starting...")
        logger.info("=" * 70)
        
        # Initialize NovaService
        await self.init_nova()
        
        # Create application
        self.application = await self.init_application()
        await self.application.initialize()
        await self.application.start()
        
        # Set global application
        _application = self.application
        logger.info("✅ Application set to global variable")
        
        # Setup webhook
        webhook_success = await self.setup_webhook()
        
        # Always start web server
        await self.start_web_server()
        
        if webhook_success:
            logger.info("✅ Webhook mode activated! Bot is ready to receive messages.")
        else:
            logger.warning("⚠️ Webhook not set properly, but web server is running.")
            logger.info("📡 Check: RAILWAY_PUBLIC_DOMAIN environment variable")
        
        logger.info("=" * 70)
        logger.info("✨ NovaService is ready!")
        logger.info(f"👑 Admin ID: {get_settings().admin_id}")
        logger.info("   Kirim /start untuk melihat semua command")
        logger.info("   Kirim /role therapist untuk panggil therapist")
        logger.info("   Kirim /role pelacur untuk panggil pelacur")
        logger.info("   Kirim /status untuk lihat status")
        logger.info("   Kirim /pause untuk jeda sesi")
        logger.info("   Kirim /resume untuk lanjutkan sesi")
        logger.info("   Kirim /batal untuk kembali ke Nova")
        logger.info("=" * 70)
        
        # Keep running
        while not self._shutdown_flag:
            await asyncio.sleep(1)
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down...")
        self._shutdown_flag = True
        
        # Stop application
        if self.application:
            try:
                await self.application.stop()
                await self.application.shutdown()
                logger.info("✅ Application stopped")
            except Exception as e:
                logger.error(f"Error stopping application: {e}", exc_info=True)
        
        # Cleanup web server
        if self._runner:
            await self._runner.cleanup()
            logger.info("✅ Web server stopped")
        
        logger.info("👋 Goodbye from NovaService!")


# =============================================================================
# ENTRY POINT
# =============================================================================

async def main():
    """Main entry point"""
    bot = NovaServiceBot()
    
    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(bot.shutdown()))
    
    try:
        await bot.start()
    except asyncio.CancelledError:
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Main error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
