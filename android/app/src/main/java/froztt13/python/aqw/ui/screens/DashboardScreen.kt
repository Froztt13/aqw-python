package froztt13.python.aqw.ui.screens

import android.Manifest
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.filled.Casino
import androidx.compose.material.icons.filled.Extension
import androidx.compose.material.icons.filled.Nightlight
import androidx.compose.material.icons.filled.People
import androidx.compose.material.icons.filled.WbSunny
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalInspectionMode
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import froztt13.python.aqw.helper.BatteryOptimizationHelper
import froztt13.python.aqw.ui.components.BackgroundOptimizationCard
import froztt13.python.aqw.ui.theme.BgDark
import froztt13.python.aqw.ui.theme.CardDark
import froztt13.python.aqw.ui.theme.DoomCrimson
import froztt13.python.aqw.ui.theme.EclipseMagenta
import froztt13.python.aqw.ui.theme.GeneralTeal
import froztt13.python.aqw.ui.theme.MyApplicationTheme
import froztt13.python.aqw.ui.theme.PrimaryPurple
import froztt13.python.aqw.ui.theme.SlaveIndigo
import froztt13.python.aqw.ui.theme.SunGold
import froztt13.python.aqw.ui.theme.TextPrimary
import froztt13.python.aqw.ui.theme.TextSecondary

@Composable
fun DashboardScreen(
    onNavigateToTemple: () -> Unit,
    onNavigateToEclipse: () -> Unit,
    onNavigateToDoom: () -> Unit,
    onNavigateToSlavery: () -> Unit,
    onNavigateToGeneral: () -> Unit,
    modifier: Modifier = Modifier
) {
    DashboardContent(
        onNavigateToTemple = onNavigateToTemple,
        onNavigateToEclipse = onNavigateToEclipse,
        onNavigateToDoom = onNavigateToDoom,
        onNavigateToSlavery = onNavigateToSlavery,
        onNavigateToGeneral = onNavigateToGeneral,
        modifier = modifier
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardContent(
    onNavigateToTemple: () -> Unit,
    onNavigateToEclipse: () -> Unit,
    onNavigateToDoom: () -> Unit,
    onNavigateToSlavery: () -> Unit,
    onNavigateToGeneral: () -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val scrollState = rememberScrollState()

    val isPreview = LocalInspectionMode.current
    var isBatteryOptIgnored by remember {
        mutableStateOf(
            if (isPreview) true else BatteryOptimizationHelper.isBatteryOptimizationIgnored(context)
        )
    }
    var hasNotificationPerm by remember {
        mutableStateOf(
            if (isPreview) true else BatteryOptimizationHelper.hasNotificationPermission(context)
        )
    }

    val notifPermissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        hasNotificationPerm = isGranted
    }

    // Refresh battery optimization state on resume
    DisposableEffect(lifecycleOwner) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_RESUME) {
                isBatteryOptIgnored =
                    BatteryOptimizationHelper.isBatteryOptimizationIgnored(context)
                hasNotificationPerm = BatteryOptimizationHelper.hasNotificationPermission(context)
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose {
            lifecycleOwner.lifecycle.removeObserver(observer)
        }
    }

    Scaffold(
        modifier = modifier.fillMaxSize(),
        containerColor = BgDark,
        topBar = {
            TopAppBar(
                title = {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Box(
                            modifier = Modifier
                                .size(10.dp)
                                .clip(CircleShape)
                                .background(PrimaryPurple)
                        )
                        Text(
                            text = "AQW BOT HUB",
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.ExtraBold,
                            letterSpacing = 0.5.sp,
                            color = TextPrimary
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = BgDark)
            )
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .verticalScroll(scrollState)
                .padding(horizontal = 18.dp),
            verticalArrangement = Arrangement.spacedBy(18.dp)
        ) {
            Text(
                text = "Select a party bot module to configure accounts and launch automation",
                style = MaterialTheme.typography.bodyMedium,
                color = TextSecondary
            )

            // Background & Battery Optimization Status Card
            BackgroundOptimizationCard(
                isBatteryOptimizationIgnored = isBatteryOptIgnored,
                hasNotificationPermission = hasNotificationPerm,
                onRequestDisableBatteryOptimization = {
                    BatteryOptimizationHelper.requestIgnoreBatteryOptimization(context)
                },
                onRequestNotificationPermission = {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                        notifPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
                    }
                }
            )

            // Bot Modules Section Header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Bot Modules",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = TextPrimary
                )
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(6.dp))
                        .background(Color(0xFF1E2438))
                        .padding(horizontal = 8.dp, vertical = 3.dp)
                ) {
                    Text(
                        text = "5 Modules",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = PrimaryPurple
                    )
                }
            }

            // Grid Row 1: Weekly Doom & Slavery Bot
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(IntrinsicSize.Max),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                BotModuleGridCard(
                    title = "Weekly Doom",
                    category = "Wheel of Doom",
                    description = "Automates weekly Gear spins across multiple accounts & detects EIODA.",
                    icon = Icons.Filled.Casino,
                    accentColor = DoomCrimson,
                    onClick = onNavigateToDoom,
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight()
                )

                BotModuleGridCard(
                    title = "Slavery Bot",
                    category = "Party Sync",
                    description = "Follows master, mimics movement, auto-zones & taunt rotation.",
                    icon = Icons.Filled.People,
                    accentColor = SlaveIndigo,
                    onClick = onNavigateToSlavery,
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight()
                )
            }

            // Grid Row 2: Temple Shrine & Maid Eclipse
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(IntrinsicSize.Max),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                BotModuleGridCard(
                    title = "Temple Shrine",
                    category = "Sun & Moon",
                    description = "4-player Midnight Sun & Solstice Moon raid party.",
                    icon = Icons.Filled.WbSunny,
                    accentColor = SunGold,
                    onClick = onNavigateToTemple,
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight()
                )

                BotModuleGridCard(
                    title = "Maid Eclipse",
                    category = "Ascended Eclipse",
                    description = "Dedicated 4-player team bot with optimized Eclipse boss taunts.",
                    icon = Icons.Filled.Nightlight,
                    accentColor = EclipseMagenta,
                    onClick = onNavigateToEclipse,
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight()
                )
            }

            // Grid Row 3: General Bot (Modular Farm Engine)
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(IntrinsicSize.Max)
            ) {
                BotModuleGridCard(
                    title = "General Bot",
                    category = "Modular Farms",
                    description = "Multi-purpose modular engine. Features Legion Revenant farm (Fealty 1-3) & Nulgath Nation farm (Larva, Uni 13, Diamonds, etc.).",
                    icon = Icons.Filled.Extension,
                    accentColor = GeneralTeal,
                    onClick = onNavigateToGeneral,
                    modifier = Modifier
                        .fillMaxWidth()
                        .fillMaxHeight()
                )
            }

            Spacer(modifier = Modifier.height(20.dp))
        }
    }
}

@Composable
fun BotModuleGridCard(
    title: String,
    category: String,
    description: String,
    icon: ImageVector,
    accentColor: Color,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier
            .clip(RoundedCornerShape(16.dp))
            .border(
                1.dp,
                accentColor.copy(alpha = 0.35f),
                RoundedCornerShape(16.dp)
            ),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = CardDark)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(14.dp),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                // Top Row: Icon Container & Arrow Button
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Box(
                        modifier = Modifier
                            .size(42.dp)
                            .clip(RoundedCornerShape(12.dp))
                            .background(accentColor.copy(alpha = 0.15f))
                            .border(
                                1.dp,
                                accentColor.copy(alpha = 0.3f),
                                RoundedCornerShape(12.dp)
                            ),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = icon,
                            contentDescription = null,
                            tint = accentColor,
                            modifier = Modifier.size(22.dp)
                        )
                    }

                    Box(
                        modifier = Modifier
                            .size(32.dp)
                            .clip(CircleShape)
                            .background(Color(0xFF161928))
                            .border(1.dp, Color(0xFF2E3350), CircleShape)
                            .clickable { onClick() },
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowForward,
                            contentDescription = "Open $title",
                            tint = accentColor,
                            modifier = Modifier.size(16.dp)
                        )
                    }
                }

                // Category Badge
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(6.dp))
                        .background(accentColor.copy(alpha = 0.12f))
                        .padding(horizontal = 6.dp, vertical = 2.dp)
                ) {
                    Text(
                        text = category.uppercase(),
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        color = accentColor,
                        letterSpacing = 0.5.sp
                    )
                }

                // Title
                Text(
                    text = title,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = TextPrimary,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )

                // Description
                Text(
                    text = description,
                    fontSize = 11.sp,
                    color = TextSecondary,
                    lineHeight = 16.sp,
                    maxLines = 3,
                    overflow = TextOverflow.Ellipsis
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Action footer pill
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(8.dp))
                    .background(accentColor.copy(alpha = 0.1f))
                    .border(
                        1.dp,
                        accentColor.copy(alpha = 0.25f),
                        RoundedCornerShape(8.dp)
                    )
                    .clickable { onClick() }
                    .padding(vertical = 6.dp, horizontal = 10.dp),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Launch Bot",
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    color = accentColor
                )
            }
        }
    }
}

@Composable
fun BotModuleHeroCard(
    title: String,
    subtitle: String,
    description: String,
    icon: ImageVector,
    accentColor: Color,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(18.dp))
            .border(
                1.5.dp,
                Color(0xFF2E3350),
                RoundedCornerShape(18.dp)
            )
            .clickable { onClick() },
        shape = RoundedCornerShape(18.dp),
        colors = CardDefaults.cardColors(containerColor = CardDark)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            // Header Row: Icon + Title + Badge
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Box(
                        modifier = Modifier
                            .size(46.dp)
                            .clip(RoundedCornerShape(12.dp))
                            .background(accentColor.copy(alpha = 0.15f))
                            .border(
                                1.dp,
                                accentColor.copy(alpha = 0.3f),
                                RoundedCornerShape(12.dp)
                            ),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = icon,
                            contentDescription = null,
                            tint = accentColor,
                            modifier = Modifier.size(24.dp)
                        )
                    }

                    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Text(
                            text = title,
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = TextPrimary
                        )
                        Text(
                            text = subtitle,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Medium,
                            color = accentColor
                        )
                    }
                }
            }

            // Description
            Text(
                text = description,
                fontSize = 12.sp,
                color = TextSecondary,
                lineHeight = 17.sp
            )

            // Action Button
            Button(
                onClick = onClick,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(44.dp),
                shape = RoundedCornerShape(10.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = accentColor.copy(alpha = 0.2f),
                    contentColor = accentColor
                ),
                border = ButtonDefaults.outlinedButtonBorder(enabled = true).copy(
                    brush = Brush.horizontalGradient(
                        listOf(
                            accentColor.copy(alpha = 0.5f),
                            accentColor.copy(alpha = 0.2f)
                        )
                    )
                )
            ) {
                Text(
                    text = "CONFIGURE & START BOT",
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    color = TextPrimary
                )
                Spacer(modifier = Modifier.width(8.dp))
                Icon(
                    imageVector = Icons.AutoMirrored.Filled.ArrowForward,
                    contentDescription = null,
                    modifier = Modifier.size(15.dp),
                    tint = accentColor
                )
            }
        }
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF0B0D14)
@Composable
private fun DashboardContentPreview() {
    MyApplicationTheme {
        DashboardContent(
            onNavigateToTemple = {},
            onNavigateToEclipse = {},
            onNavigateToDoom = {},
            onNavigateToSlavery = {},
            onNavigateToGeneral = {}
        )
    }
}
