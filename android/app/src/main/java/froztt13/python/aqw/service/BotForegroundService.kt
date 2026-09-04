package froztt13.python.aqw.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.core.app.ServiceCompat
import androidx.core.content.ContextCompat
import froztt13.python.aqw.MainActivity
import froztt13.python.aqw.R
import froztt13.python.aqw.helper.BotHelper
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

class BotForegroundService : Service() {

    private val serviceScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var statusMonitorJob: Job? = null
    private var currentBotTitle: String = "AQW Bot"
    private var currentBotSubtitle: String = "Party active in background"

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val action = intent?.action ?: ACTION_START

        when (action) {
            ACTION_STOP -> {
                Log.d(TAG, "Received ACTION_STOP -> stopping bots and foreground service")
                serviceScope.launch {
                    try {
                        BotHelper.stopParty("temple_stop_party")
                        BotHelper.stopParty("eclipse_stop_party")
                    } catch (e: Exception) {
                        Log.e(TAG, "Error stopping bots: ${e.message}")
                    } finally {
                        stopForegroundNotification()
                    }
                }
                return START_NOT_STICKY
            }

            ACTION_START -> {
                val title = intent?.getStringExtra(EXTRA_BOT_TITLE) ?: "AQW Bot"
                val subtitle =
                    intent?.getStringExtra(EXTRA_BOT_SUBTITLE) ?: "Party active in background"
                currentBotTitle = title
                currentBotSubtitle = subtitle

                val notification = buildNotification(currentBotTitle, currentBotSubtitle)
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                    ServiceCompat.startForeground(
                        this,
                        NOTIFICATION_ID,
                        notification,
                        ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC
                    )
                } else {
                    startForeground(NOTIFICATION_ID, notification)
                }

                startStatusMonitor()
                return START_STICKY
            }

            ACTION_UPDATE -> {
                val title = intent?.getStringExtra(EXTRA_BOT_TITLE) ?: currentBotTitle
                val subtitle = intent?.getStringExtra(EXTRA_BOT_SUBTITLE) ?: currentBotSubtitle
                currentBotTitle = title
                currentBotSubtitle = subtitle

                val notification = buildNotification(currentBotTitle, currentBotSubtitle)
                val manager = getSystemService(NOTIFICATION_SERVICE) as? NotificationManager
                manager?.notify(NOTIFICATION_ID, notification)
                return START_STICKY
            }
        }

        return START_STICKY
    }

    private fun startStatusMonitor() {
        statusMonitorJob?.cancel()
        statusMonitorJob = serviceScope.launch {
            // Give the bot a 3-second grace window to start up
            delay(3000)
            while (isActive) {
                delay(2000)
                try {
                    val templeStatusJson = BotHelper.getStatus("temple_get_status")
                    val eclipseStatusJson = BotHelper.getStatus("eclipse_get_status")

                    val templeSlots =
                        templeStatusJson?.let { BotHelper.parseSlotTelemetryMap(it) } ?: emptyMap()
                    val eclipseSlots =
                        eclipseStatusJson?.let { BotHelper.parseSlotTelemetryMap(it) } ?: emptyMap()

                    val isTempleRunning = templeSlots.values.any { it.running }
                    val isEclipseRunning = eclipseSlots.values.any { it.running }

                    if (!isTempleRunning && !isEclipseRunning) {
                        Log.d(TAG, "No active bots running. Stopping foreground service.")
                        stopForegroundNotification()
                        break
                    }

                    val activeTitle =
                        if (isTempleRunning) "Temple Shrine Bot" else "Maid Eclipse Bot"
                    val stats = if (isTempleRunning) {
                        templeStatusJson?.let { BotHelper.parsePartyStats(it) }
                    } else {
                        eclipseStatusJson?.let { BotHelper.parsePartyStats(it) }
                    }

                    val statusText = if (stats != null && stats.timeRunning > 0L) {
                        "Running: ${stats.formattedTime} | Cleared: ${stats.clearedCount}"
                    } else {
                        "Party active in background"
                    }

                    currentBotTitle = activeTitle
                    currentBotSubtitle = statusText

                    val notification = buildNotification(currentBotTitle, currentBotSubtitle)
                    val manager =
                        getSystemService(NOTIFICATION_SERVICE) as? NotificationManager
                    manager?.notify(NOTIFICATION_ID, notification)
                } catch (e: Exception) {
                    Log.w(TAG, "Error in background status loop: ${e.message}")
                }
            }
        }
    }

    private fun buildNotification(title: String, contentText: String): Notification {
        val openAppIntent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val openAppPendingIntent = PendingIntent.getActivity(
            this,
            0,
            openAppIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val stopIntent = Intent(this, BotForegroundService::class.java).apply {
            action = ACTION_STOP
        }
        val stopPendingIntent = PendingIntent.getService(
            this,
            1,
            stopIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(title)
            .setContentText(contentText)
            .setSmallIcon(R.mipmap.ic_launcher)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .setContentIntent(openAppPendingIntent)
            .addAction(
                android.R.drawable.ic_menu_close_clear_cancel,
                "Stop Bot",
                stopPendingIntent
            )
            .build()
    }

    private fun stopForegroundNotification() {
        statusMonitorJob?.cancel()
        statusMonitorJob = null
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                CHANNEL_NAME,
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Shows live running status when AQW Party Bot is active"
                setShowBadge(false)
                lockscreenVisibility = Notification.VISIBILITY_PUBLIC
            }
            val manager = getSystemService(NOTIFICATION_SERVICE) as? NotificationManager
            manager?.createNotificationChannel(channel)
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        statusMonitorJob?.cancel()
        serviceScope.cancel()
        Log.d(TAG, "BotForegroundService destroyed")
    }

    companion object {
        private const val TAG = "BotForegroundService"
        const val CHANNEL_ID = "aqw_bot_running_channel"
        const val CHANNEL_NAME = "AQW Bot Running Service"
        const val NOTIFICATION_ID = 1337

        const val ACTION_START = "froztt13.python.aqw.action.START_BOT_SERVICE"
        const val ACTION_STOP = "froztt13.python.aqw.action.STOP_BOT_SERVICE"
        const val ACTION_UPDATE = "froztt13.python.aqw.action.UPDATE_BOT_SERVICE"

        const val EXTRA_BOT_TITLE = "extra_bot_title"
        const val EXTRA_BOT_SUBTITLE = "extra_bot_subtitle"

        fun start(
            context: Context,
            botTitle: String = "AQW Bot",
            botSubtitle: String = "Party starting..."
        ) {
            val intent = Intent(context, BotForegroundService::class.java).apply {
                action = ACTION_START
                putExtra(EXTRA_BOT_TITLE, botTitle)
                putExtra(EXTRA_BOT_SUBTITLE, botSubtitle)
            }
            try {
                ContextCompat.startForegroundService(context, intent)
            } catch (e: Exception) {
                Log.e(TAG, "Failed to start foreground service: ${e.message}", e)
            }
        }

        fun update(context: Context, botTitle: String, botSubtitle: String) {
            val intent = Intent(context, BotForegroundService::class.java).apply {
                action = ACTION_UPDATE
                putExtra(EXTRA_BOT_TITLE, botTitle)
                putExtra(EXTRA_BOT_SUBTITLE, botSubtitle)
            }
            try {
                context.startService(intent)
            } catch (e: Exception) {
                Log.w(TAG, "Failed to send update to service: ${e.message}")
            }
        }

        fun stop(context: Context) {
            val intent = Intent(context, BotForegroundService::class.java).apply {
                action = ACTION_STOP
            }
            try {
                context.startService(intent)
            } catch (e: Exception) {
                Log.w(TAG, "Failed to stop foreground service: ${e.message}")
            }
        }
    }
}
