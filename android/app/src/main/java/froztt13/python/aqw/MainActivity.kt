package froztt13.python.aqw

import android.os.Bundle
import android.os.PowerManager
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.systemBarsPadding
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import froztt13.python.aqw.ui.screens.DashboardScreen
import froztt13.python.aqw.ui.screens.EclipseScreen
import froztt13.python.aqw.ui.screens.SlaveryScreen
import froztt13.python.aqw.ui.screens.TempleScreen
import froztt13.python.aqw.ui.screens.WeeklyDoomBotScreen
import froztt13.python.aqw.ui.theme.BgDark
import froztt13.python.aqw.ui.theme.MyApplicationTheme
import android.graphics.Color as AndroidColor

enum class AppScreen {
    DASHBOARD,
    TEMPLE,
    ECLIPSE,
    WEEKLY_DOOM,
    SLAVERY
}

class MainActivity : ComponentActivity() {

    private var wakeLock: PowerManager.WakeLock? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge(
            statusBarStyle = SystemBarStyle.dark(AndroidColor.TRANSPARENT),
            navigationBarStyle = SystemBarStyle.dark(AndroidColor.TRANSPARENT)
        )

        // 1. Initialize Python Runtime via Chaquopy
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }

        // Set persistent storage folder for Python configs
        try {
            val py = Python.getInstance()
            val pySys = py.getModule("os")
            pySys.get("environ")?.callAttr("__setitem__", "ANDROID_DATA_DIR", filesDir.absolutePath)
        } catch (e: Exception) {
            Log.e("MainActivity", "Error setting ANDROID_DATA_DIR: ${e.message}")
        }

        // 2. Acquire Partial WakeLock to keep game socket active
        try {
            val powerManager = getSystemService(POWER_SERVICE) as PowerManager
            wakeLock = powerManager.newWakeLock(
                PowerManager.PARTIAL_WAKE_LOCK,
                "AQWBot:BackgroundWakeLock"
            )
            wakeLock?.acquire(24 * 60 * 60 * 1000L) // 24 hours
        } catch (e: Exception) {
            Log.w("MainActivity", "Could not acquire WakeLock: ${e.message}")
        }

        setContent {
            MyApplicationTheme {
                Surface(
                    modifier = Modifier
                        .fillMaxSize()
                        .systemBarsPadding(),
                    color = BgDark
                ) {
                    MainAppScreen()
                }
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        try {
            if (wakeLock?.isHeld == true) {
                wakeLock?.release()
            }
        } catch (e: Exception) {
            Log.w("MainActivity", "Error releasing WakeLock: ${e.message}")
        }
    }
}

@Composable
fun MainAppScreen() {
    var currentScreen by remember { mutableStateOf(AppScreen.DASHBOARD) }

    // Intercept back button when not on dashboard
    BackHandler(enabled = currentScreen != AppScreen.DASHBOARD) {
        currentScreen = AppScreen.DASHBOARD
    }

    AnimatedContent(
        targetState = currentScreen,
        transitionSpec = { fadeIn() togetherWith fadeOut() },
        label = "ScreenTransition"
    ) { targetScreen ->
        when (targetScreen) {
            AppScreen.DASHBOARD -> DashboardScreen(
                onNavigateToTemple = { currentScreen = AppScreen.TEMPLE },
                onNavigateToEclipse = { currentScreen = AppScreen.ECLIPSE },
                onNavigateToDoom = { currentScreen = AppScreen.WEEKLY_DOOM },
                onNavigateToSlavery = { currentScreen = AppScreen.SLAVERY }
            )

            AppScreen.TEMPLE -> TempleScreen(
                onBack = { currentScreen = AppScreen.DASHBOARD }
            )

            AppScreen.ECLIPSE -> EclipseScreen(
                onBack = { currentScreen = AppScreen.DASHBOARD }
            )

            AppScreen.WEEKLY_DOOM -> WeeklyDoomBotScreen(
                onBack = { currentScreen = AppScreen.DASHBOARD }
            )

            AppScreen.SLAVERY -> SlaveryScreen(
                onBack = { currentScreen = AppScreen.DASHBOARD }
            )
        }
    }
}