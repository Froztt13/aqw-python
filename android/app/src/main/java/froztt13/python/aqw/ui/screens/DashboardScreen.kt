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
import androidx.compose.material.icons.automirrored.filled.OpenInNew
import androidx.compose.material.icons.filled.Casino
import androidx.compose.material.icons.filled.Code
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
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.collectAsState
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
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.viewmodel.compose.viewModel
import froztt13.python.aqw.data.BotSummary
import froztt13.python.aqw.data.HubOverview


import froztt13.python.aqw.helper.BatteryOptimizationHelper
import froztt13.python.aqw.ui.components.BackgroundOptimizationCard
import froztt13.python.aqw.ui.components.DefaultTopBar
import froztt13.python.aqw.ui.theme.BgDark
import froztt13.python.aqw.ui.theme.BorderDark
import froztt13.python.aqw.ui.theme.CardDark
import froztt13.python.aqw.ui.theme.DoomCrimson
import froztt13.python.aqw.ui.theme.EclipseMagenta
import froztt13.python.aqw.ui.theme.GeneralTeal
import froztt13.python.aqw.ui.theme.MyApplicationTheme
import froztt13.python.aqw.ui.theme.PrimaryPurple
import froztt13.python.aqw.ui.theme.SlaveIndigo
import froztt13.python.aqw.ui.theme.SuccessGreen
import froztt13.python.aqw.ui.theme.SunGold
import froztt13.python.aqw.ui.theme.TextMuted
import froztt13.python.aqw.ui.theme.TextPrimary
import froztt13.python.aqw.ui.theme.TextSecondary
import froztt13.python.aqw.viewmodel.DashboardViewModel


@Composable
fun DashboardScreen(
    onNavigateToTemple: () -> Unit,
    onNavigateToEclipse: () -> Unit,
    onNavigateToDoom: () -> Unit,
    onNavigateToSlavery: () -> Unit,
    onNavigateToGeneral: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: DashboardViewModel = viewModel()
) {
    val hubOverview by viewModel.hubOverview.collectAsState()

    DashboardContent(
        hubOverview = hubOverview,
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
    modifier: Modifier = Modifier,
    hubOverview: HubOverview = HubOverview(),
    onNavigateToTemple: () -> Unit,
    onNavigateToEclipse: () -> Unit,
    onNavigateToDoom: () -> Unit,
    onNavigateToSlavery: () -> Unit,
    onNavigateToGeneral: () -> Unit
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
            DefaultTopBar(
                title = "AQW BOT HUB",
                version = "0.1",
                statusDotColor = if (hubOverview.anyRunning) SuccessGreen else PrimaryPurple
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

            // Active Bot Sessions Banner (shown when one or more bots are running)
            if (hubOverview.anyRunning) {
                ActiveBotSessionsCard(
                    hubOverview = hubOverview,
                    onNavigateToTemple = onNavigateToTemple,
                    onNavigateToEclipse = onNavigateToEclipse,
                    onNavigateToDoom = onNavigateToDoom,
                    onNavigateToSlavery = onNavigateToSlavery,
                    onNavigateToGeneral = onNavigateToGeneral
                )
            }

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
                        .background(
                            if (hubOverview.anyRunning) SuccessGreen.copy(alpha = 0.15f)
                            else Color(0xFF1E2438)
                        )
                        .border(
                            1.dp,
                            if (hubOverview.anyRunning) SuccessGreen.copy(alpha = 0.4f)
                            else Color.Transparent,
                            RoundedCornerShape(6.dp)
                        )
                        .padding(horizontal = 8.dp, vertical = 3.dp)
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(4.dp)
                    ) {
                        if (hubOverview.anyRunning) {
                            Box(
                                modifier = Modifier
                                    .size(6.dp)
                                    .clip(CircleShape)
                                    .background(SuccessGreen)
                            )
                        }
                        Text(
                            text = if (hubOverview.anyRunning) "${hubOverview.activeCount} RUNNING" else "5 Modules",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.SemiBold,
                            color = if (hubOverview.anyRunning) SuccessGreen else PrimaryPurple
                        )
                    }
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
                    isRunning = hubOverview.doom.running,
                    runningDetail = if (hubOverview.doom.running) {
                        if (hubOverview.doom.currentUsername.isNotEmpty()) {
                            "${hubOverview.doom.currentUsername} • ${hubOverview.doom.formattedTime}"
                        } else {
                            hubOverview.doom.formattedTime
                        }
                    } else null,
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
                    isRunning = hubOverview.slavery.running,
                    runningDetail = if (hubOverview.slavery.running) {
                        "${hubOverview.slavery.count} Active • ${hubOverview.slavery.formattedTime}"
                    } else null,
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
                    isRunning = hubOverview.temple.running,
                    runningDetail = if (hubOverview.temple.running) {
                        "${hubOverview.temple.count} Active • ${hubOverview.temple.formattedTime}"
                    } else null,
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
                    isRunning = hubOverview.eclipse.running,
                    runningDetail = if (hubOverview.eclipse.running) {
                        "${hubOverview.eclipse.count} Active • ${hubOverview.eclipse.formattedTime}"
                    } else null,
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
                    description = "Multi-purpose modular engine. Features Legion Revenant (Fealty 1-3), Nulgath Nation (Larva), & Void Aura (NSOD Quest 4432).",
                    icon = Icons.Filled.Extension,
                    accentColor = GeneralTeal,
                    onClick = onNavigateToGeneral,
                    isRunning = hubOverview.general.running,
                    runningDetail = if (hubOverview.general.running) {
                        "${if (hubOverview.general.subModule.isNotEmpty()) hubOverview.general.subModule else "Farm"} • ${hubOverview.general.formattedTime}"
                    } else null,
                    modifier = Modifier
                        .fillMaxWidth()
                        .fillMaxHeight()
                )
            }

            // Project Source / GitHub Attribution Card
            val uriHandler = LocalUriHandler.current
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(14.dp))
                    .border(1.dp, BorderDark, RoundedCornerShape(14.dp))
                    .clickable {
                        try {
                            uriHandler.openUri("https://github.com/Froztt13/aqw-python")
                        } catch (_: Exception) {
                        }
                    },
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = CardDark)
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(14.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .size(38.dp)
                            .clip(RoundedCornerShape(10.dp))
                            .background(PrimaryPurple.copy(alpha = 0.15f)),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = Icons.Filled.Code,
                            contentDescription = "Source Code",
                            tint = PrimaryPurple,
                            modifier = Modifier.size(20.dp)
                        )
                    }

                    Column(
                        modifier = Modifier.weight(1f),
                        verticalArrangement = Arrangement.spacedBy(2.dp)
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(6.dp)
                        ) {
                            Text(
                                text = "Based on aqw-python",
                                style = MaterialTheme.typography.bodyMedium,
                                fontWeight = FontWeight.SemiBold,
                                color = TextPrimary
                            )
                            Box(
                                modifier = Modifier
                                    .clip(RoundedCornerShape(4.dp))
                                    .background(PrimaryPurple.copy(alpha = 0.18f))
                                    .padding(horizontal = 6.dp, vertical = 2.dp)
                            ) {
                                Text(
                                    text = "GitHub",
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = PrimaryPurple
                                )
                            }
                        }
                        Text(
                            text = "https://github.com/Froztt13/aqw-python",
                            style = MaterialTheme.typography.bodySmall,
                            color = TextMuted,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                    }

                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.OpenInNew,
                        contentDescription = "Open Link",
                        tint = TextSecondary,
                        modifier = Modifier.size(18.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(20.dp))
        }
    }
}

@Composable
fun ActiveBotSessionsCard(
    hubOverview: HubOverview,
    onNavigateToTemple: () -> Unit,
    onNavigateToEclipse: () -> Unit,
    onNavigateToDoom: () -> Unit,
    onNavigateToSlavery: () -> Unit,
    onNavigateToGeneral: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .border(
                1.5.dp,
                SuccessGreen.copy(alpha = 0.5f),
                RoundedCornerShape(16.dp)
            ),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFF0F1A1B)
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            // Header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .size(10.dp)
                            .clip(CircleShape)
                            .background(SuccessGreen)
                    )
                    Text(
                        text = "ACTIVE BOT SESSION${if (hubOverview.activeCount > 1) "S" else ""}",
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.Bold,
                        color = SuccessGreen,
                        letterSpacing = 0.5.sp
                    )
                }

                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(6.dp))
                        .background(SuccessGreen.copy(alpha = 0.18f))
                        .padding(horizontal = 8.dp, vertical = 3.dp)
                ) {
                    Text(
                        text = "${hubOverview.activeCount} RUNNING",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        color = SuccessGreen
                    )
                }
            }

            // Running Bot Rows
            if (hubOverview.doom.running) {
                ActiveBotItemRow(
                    title = "Weekly Doom",
                    details = if (hubOverview.doom.currentUsername.isNotEmpty()) {
                        "Account: ${hubOverview.doom.currentUsername} • ${hubOverview.doom.formattedTime}"
                    } else {
                        "Running • ${hubOverview.doom.formattedTime}"
                    },
                    accentColor = DoomCrimson,
                    onClick = onNavigateToDoom
                )
            }

            if (hubOverview.slavery.running) {
                ActiveBotItemRow(
                    title = "Slavery Bot",
                    details = "${hubOverview.slavery.count} party accounts active • ${hubOverview.slavery.formattedTime}",
                    accentColor = SlaveIndigo,
                    onClick = onNavigateToSlavery
                )
            }

            if (hubOverview.temple.running) {
                ActiveBotItemRow(
                    title = "Temple Shrine",
                    details = "${hubOverview.temple.count} accounts active • ${hubOverview.temple.formattedTime}",
                    accentColor = SunGold,
                    onClick = onNavigateToTemple
                )
            }

            if (hubOverview.eclipse.running) {
                ActiveBotItemRow(
                    title = "Maid Eclipse",
                    details = "${hubOverview.eclipse.count} accounts active • ${hubOverview.eclipse.formattedTime}",
                    accentColor = EclipseMagenta,
                    onClick = onNavigateToEclipse
                )
            }

            if (hubOverview.general.running) {
                ActiveBotItemRow(
                    title = "General Bot",
                    details = "${hubOverview.general.subModule.ifEmpty { "Farm" }} • ${hubOverview.general.formattedTime}",
                    accentColor = GeneralTeal,
                    onClick = onNavigateToGeneral
                )
            }
        }
    }
}

@Composable
private fun ActiveBotItemRow(
    title: String,
    details: String,
    accentColor: Color,
    onClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(10.dp))
            .background(CardDark.copy(alpha = 0.75f))
            .border(1.dp, BorderDark, RoundedCornerShape(10.dp))
            .clickable { onClick() }
            .padding(horizontal = 12.dp, vertical = 10.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Row(
            modifier = Modifier.weight(1f),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Box(
                modifier = Modifier
                    .size(8.dp)
                    .clip(CircleShape)
                    .background(accentColor)
            )
            Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text(
                    text = title,
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.Bold,
                    color = TextPrimary
                )
                Text(
                    text = details,
                    fontSize = 11.sp,
                    color = TextSecondary,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
            }
        }

        Box(
            modifier = Modifier
                .clip(RoundedCornerShape(6.dp))
                .background(accentColor.copy(alpha = 0.18f))
                .border(1.dp, accentColor.copy(alpha = 0.35f), RoundedCornerShape(6.dp))
                .padding(horizontal = 10.dp, vertical = 5.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                Text(
                    text = "Open",
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    color = accentColor
                )
                Icon(
                    imageVector = Icons.AutoMirrored.Filled.ArrowForward,
                    contentDescription = null,
                    tint = accentColor,
                    modifier = Modifier.size(12.dp)
                )
            }
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
    modifier: Modifier = Modifier,
    isRunning: Boolean = false,
    runningDetail: String? = null
) {
    Card(
        modifier = modifier
            .clip(RoundedCornerShape(16.dp))
            .border(
                width = if (isRunning) 1.5.dp else 1.dp,
                color = if (isRunning) accentColor else accentColor.copy(alpha = 0.35f),
                shape = RoundedCornerShape(16.dp)
            ),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = if (isRunning) accentColor.copy(alpha = 0.08f) else CardDark
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(14.dp),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                // Top Row: Icon Container & Active Pill / Arrow Button
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
                                accentColor.copy(alpha = if (isRunning) 0.6f else 0.3f),
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

                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(6.dp)
                    ) {
                        if (isRunning) {
                            Box(
                                modifier = Modifier
                                    .clip(RoundedCornerShape(6.dp))
                                    .background(SuccessGreen.copy(alpha = 0.2f))
                                    .border(
                                        1.dp,
                                        SuccessGreen.copy(alpha = 0.6f),
                                        RoundedCornerShape(6.dp)
                                    )
                                    .padding(horizontal = 6.dp, vertical = 3.dp)
                            ) {
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                                ) {
                                    Box(
                                        modifier = Modifier
                                            .size(6.dp)
                                            .clip(CircleShape)
                                            .background(SuccessGreen)
                                            .clickable { onClick() }
                                    )
                                    Text(
                                        text = "ACTIVE",
                                        fontSize = 9.sp,
                                        fontWeight = FontWeight.Bold,
                                        color = SuccessGreen,
                                        letterSpacing = 0.5.sp
                                    )
                                }
                            }
                        } else {
                            Box(
                                modifier = Modifier
                                    .size(32.dp)
                                    .clip(CircleShape)
                                    .background(Color(0xFF161928))
                                    .border(
                                        1.dp,
                                        Color(0xFF2E3350),
                                        CircleShape
                                    )
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
                    }
                }

                // Category Badge & Running Detail
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
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

                    if (isRunning && !runningDetail.isNullOrBlank()) {
                        Text(
                            text = runningDetail,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.SemiBold,
                            color = SuccessGreen,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                    }
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
                    .background(
                        if (isRunning) accentColor.copy(alpha = 0.22f) else accentColor.copy(alpha = 0.1f)
                    )
                    .border(
                        1.dp,
                        if (isRunning) accentColor.copy(alpha = 0.6f) else accentColor.copy(alpha = 0.25f),
                        RoundedCornerShape(8.dp)
                    )
                    .clickable { onClick() }
                    .padding(vertical = 6.dp, horizontal = 10.dp),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
            ) {
                if (isRunning) {
                    Box(
                        modifier = Modifier
                            .size(6.dp)
                            .clip(CircleShape)
                            .background(SuccessGreen)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = "RUNNING • OPEN",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        color = TextPrimary
                    )
                } else {
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

@Preview(name = "Dashboard - Idle", showBackground = true, backgroundColor = 0xFF0B0D14)
@Composable
private fun DashboardContentIdlePreview() {
    MyApplicationTheme {
        DashboardContent(
            hubOverview = HubOverview(),
            onNavigateToTemple = {},
            onNavigateToEclipse = {},
            onNavigateToDoom = {},
            onNavigateToSlavery = {},
            onNavigateToGeneral = {}
        )
    }
}

@Preview(name = "Dashboard - Active Bots", showBackground = true, backgroundColor = 0xFF0B0D14)
@Composable
private fun DashboardContentActivePreview() {
    val sampleActiveOverview = HubOverview(
        temple = BotSummary(
            running = true,
            count = 4,
            members = listOf("Slot1_Lead", "Slot2_DPS", "Slot3_Buff", "Slot4_Heal"),
            timeRunning = 3725L // 01:02:05
        ),
        general = BotSummary(
            running = true,
            currentUsername = "HeroFarmer",
            subModule = "Legion Revenant",
            task = "Fealty 1",
            timeRunning = 1450L // 24:10
        ),
        doom = BotSummary(
            running = false
        ),
        eclipse = BotSummary(
            running = false
        ),
        slavery = BotSummary(
            running = false
        )
    )

    MyApplicationTheme {
        DashboardContent(
            hubOverview = sampleActiveOverview,
            onNavigateToTemple = {},
            onNavigateToEclipse = {},
            onNavigateToDoom = {},
            onNavigateToSlavery = {},
            onNavigateToGeneral = {}
        )
    }
}

@Preview(name = "Active Bot Sessions Banner", showBackground = true, backgroundColor = 0xFF0B0D14)
@Composable
private fun ActiveBotSessionsCardPreview() {
    val sampleActiveOverview = HubOverview(
        temple = BotSummary(
            running = true,
            count = 4,
            members = listOf("Slot1_Lead", "Slot2_DPS", "Slot3_Buff", "Slot4_Heal"),
            timeRunning = 1845L
        ),
        doom = BotSummary(
            running = true,
            currentUsername = "DoomFarmer99",
            timeRunning = 340L
        ),
        general = BotSummary(
            running = true,
            currentUsername = "HeroFarmer",
            subModule = "Void Aura",
            timeRunning = 7200L
        )
    )

    MyApplicationTheme {
        Box(modifier = Modifier.padding(16.dp)) {
            ActiveBotSessionsCard(
                hubOverview = sampleActiveOverview,
                onNavigateToTemple = {},
                onNavigateToEclipse = {},
                onNavigateToDoom = {},
                onNavigateToSlavery = {},
                onNavigateToGeneral = {}
            )
        }
    }
}

@Preview(
    name = "Grid Card Active vs Idle",
    showBackground = true,
    backgroundColor = 0xFF0B0D14,
    heightDp = 300
)
@Composable
private fun BotModuleGridCardComparisonPreview() {
    MyApplicationTheme {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            BotModuleGridCard(
                title = "Weekly Doom",
                category = "Wheel of Doom",
                description = "Automates weekly Gear spins across multiple accounts & detects EIODA.",
                icon = Icons.Filled.Casino,
                accentColor = DoomCrimson,
                onClick = {},
                isRunning = false,
                modifier = Modifier.weight(1f)
            )

            BotModuleGridCard(
                title = "Temple Shrine",
                category = "Sun & Moon",
                description = "4-player Midnight Sun & Solstice Moon raid party.",
                icon = Icons.Filled.WbSunny,
                accentColor = SunGold,
                onClick = {},
                isRunning = true,
                runningDetail = "4 Active • 00:24:18",
                modifier = Modifier.weight(1f)
            )
        }
    }
}

