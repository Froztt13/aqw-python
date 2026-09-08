package froztt13.python.aqw.ui.screens

import android.Manifest
import android.os.Build
import android.widget.Toast
import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Bolt
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.DragHandle
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material.icons.filled.WaterDrop
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.ScrollableTabRow
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRowDefaults
import androidx.compose.material3.TabRowDefaults.tabIndicatorOffset
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalInspectionMode
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import froztt13.python.aqw.R
import froztt13.python.aqw.data.LogEntry
import froztt13.python.aqw.data.MonsterTelemetry
import froztt13.python.aqw.data.PartyStats
import froztt13.python.aqw.data.Skill
import froztt13.python.aqw.data.SlaveSlotConfig
import froztt13.python.aqw.data.SlaveryConfig
import froztt13.python.aqw.data.SlotTelemetry
import froztt13.python.aqw.data.ThresholdType
import froztt13.python.aqw.helper.BatteryOptimizationHelper
import froztt13.python.aqw.service.BotForegroundService
import froztt13.python.aqw.ui.components.BotSessionStatsBar
import froztt13.python.aqw.ui.components.DefaultTopBar
import froztt13.python.aqw.ui.components.LiveLogConsole
import froztt13.python.aqw.ui.components.MonsterTelemetryCard
import froztt13.python.aqw.ui.theme.BgDark
import froztt13.python.aqw.ui.theme.CardDark
import froztt13.python.aqw.ui.theme.ErrorRed
import froztt13.python.aqw.ui.theme.MoonCyan
import froztt13.python.aqw.ui.theme.MyApplicationTheme
import froztt13.python.aqw.ui.theme.SlaveIndigo
import froztt13.python.aqw.ui.theme.SuccessGreen
import froztt13.python.aqw.ui.theme.SunGold
import froztt13.python.aqw.ui.theme.TextMuted
import froztt13.python.aqw.ui.theme.TextPrimary
import froztt13.python.aqw.ui.theme.TextSecondary
import froztt13.python.aqw.viewmodel.SlaveryViewModel
import kotlinx.coroutines.launch
import sh.calvin.reorderable.ReorderableColumn

val AUTO_ZONE_OPTIONS =
    listOf("none", "Astral Empyrean", "Dark Carnax", "Ultra Dage", "Queen Iona", "Vordred")
val OPERATOR_OPTIONS = listOf("<", ">")

@Composable
fun SlaveryScreen(
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: SlaveryViewModel = viewModel()
) {
    val context = LocalContext.current
    val config by viewModel.slaveryConfig.collectAsState()
    val telemetryMap by viewModel.slaveryStatus.collectAsState()
    val partyStats by viewModel.partyStats.collectAsState()
    val isRunning by viewModel.isRunning.collectAsState()
    val logs by viewModel.slaveryLogs.collectAsState()

    var isSettingsOpen by remember { mutableStateOf(false) }

    val notifPermissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { /* Ignored */ }

    BackHandler(enabled = isSettingsOpen) {
        isSettingsOpen = false
    }

    if (isSettingsOpen) {
        SlaverySettingsScreen(
            config = config,
            isRunning = isRunning,
            onBack = { isSettingsOpen = false },
            onUpdateGlobalSettings = { server, followPlayer, defaultRoomNumber, copyWalk, autoZone, targetsPriority, whitelist, lockedZones ->
                viewModel.updateGlobalSettings(
                    server = server,
                    followPlayer = followPlayer,
                    defaultRoomNumber = defaultRoomNumber,
                    copyWalk = copyWalk,
                    autoZone = autoZone,
                    targetsPriority = targetsPriority,
                    whitelist = whitelist,
                    lockedZones = lockedZones
                )
            },
            onResetSettings = {
                viewModel.resetSlaveryConfig()
            },
            modifier = modifier
        )
    } else {
        SlaveryContent(
            config = config,
            telemetryMap = telemetryMap,
            partyStats = partyStats,
            logs = logs,
            isRunning = isRunning,
            onBack = onBack,
            onOpenSettings = { isSettingsOpen = true },
            onUpdateSlot = { slotKey, slotConfig ->
                viewModel.updateSlot(slotKey, slotConfig)
            },
            onStartParty = {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                    if (!BatteryOptimizationHelper.hasNotificationPermission(context)) {
                        notifPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
                    }
                }
                viewModel.startSlavery { success, error ->
                    if (success) {
                        BotForegroundService.start(
                            context = context,
                            botTitle = "Slavery Bot",
                            botSubtitle = "Following: ${config.followPlayer.ifEmpty { "Master" }}"
                        )
                    } else {
                        Toast.makeText(context, error ?: "Failed to start bot", Toast.LENGTH_LONG)
                            .show()
                    }
                }
            },
            onStopParty = {
                viewModel.stopSlavery()
                BotForegroundService.stop(context)
            },
            onClearLogs = {
                viewModel.clearLogs()
            },
            modifier = modifier
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SlaveryContent(
    config: SlaveryConfig,
    telemetryMap: Map<String, SlotTelemetry>,
    partyStats: PartyStats,
    logs: List<LogEntry>,
    isRunning: Boolean,
    onBack: () -> Unit,
    onOpenSettings: () -> Unit,
    onUpdateSlot: (slotKey: String, slotConfig: SlaveSlotConfig) -> Unit,
    onStartParty: () -> Unit,
    onStopParty: () -> Unit,
    onClearLogs: () -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val scrollState = rememberScrollState()
    val coroutineScope = rememberCoroutineScope()

    val slotKeys = listOf("slot1", "slot2", "slot3", "slot4")
    val slotLabels = listOf("Slot 1", "Slot 2", "Slot 3", "Slot 4")
    val slotFullTitles = listOf(
        "Slot 1",
        "Slot 2",
        "Slot 3",
        "Slot 4"
    )

    val pagerState = rememberPagerState(pageCount = { 4 })

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

    Scaffold(
        modifier = modifier.fillMaxSize(),
        containerColor = BgDark,
        topBar = {
            DefaultTopBar(
                title = "Slavery Bot",
                statusDotColor = SlaveIndigo,
                onBack = onBack
            )
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .verticalScroll(scrollState)
                .padding(horizontal = 16.dp, vertical = 8.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            // Master Account Follow Banner Card
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, SlaveIndigo.copy(alpha = 0.4f), RoundedCornerShape(16.dp))
                    .clickable(enabled = !isRunning) { onOpenSettings() },
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = CardDark)
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 8.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(10.dp)
                        ) {
                            Image(
                                painter = painterResource(R.drawable.icon),
                                contentDescription = null,
                                alpha = 0.9f,
                                modifier = Modifier
                                    .size(38.dp)
                                    .clip(CircleShape)
                            )
                            Column {
                                Text(
                                    text = "FOLLOWING MASTER",
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = TextSecondary,
                                    letterSpacing = 1.sp
                                )
                                Text(
                                    text = config.followPlayer.ifEmpty { "None (Not Set)" },
                                    fontSize = 16.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = if (config.followPlayer.isNotEmpty()) Color.White else TextMuted
                                )
                            }
                        }

                        IconButton(
                            onClick = onOpenSettings,
                            enabled = !isRunning,
                        ) {
                            Icon(
                                imageVector = Icons.Filled.Settings,
                                contentDescription = "Settings",
                                tint = SlaveIndigo,
                                modifier = Modifier.size(20.dp)
                            )
                        }
                    }

                    // Status Chips Row
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(6.dp)
                    ) {
                        // Server
                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(6.dp))
                                .background(Color(0xFF161928))
                                .padding(horizontal = 8.dp, vertical = 4.dp)
                        ) {
                            Text(
                                text = "${config.server.ifEmpty { "Artix" }} #${config.defaultRoomNumber}",
                                fontSize = 11.sp,
                                color = TextPrimary
                            )
                        }

                        // Copy Walk
                        /*Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(6.dp))
                                .background(
                                    if (config.copyWalk) SuccessGreen.copy(alpha = 0.15f)
                                    else Color(0xFF161928)
                                )
                                .padding(horizontal = 8.dp, vertical = 4.dp)
                        ) {
                            Text(
                                text = if (config.copyWalk) "Copy Walk: ON" else "Copy Walk: OFF",
                                fontSize = 11.sp,
                                color = if (config.copyWalk) SuccessGreen else TextMuted,
                                fontWeight = FontWeight.SemiBold
                            )
                        }*/

                        // Auto Zone if set
                        /*if (config.autoZone.isNotEmpty() && config.autoZone != "none") {
                            Box(
                                modifier = Modifier
                                    .clip(RoundedCornerShape(6.dp))
                                    .background(MoonCyan.copy(alpha = 0.15f))
                                    .padding(horizontal = 8.dp, vertical = 4.dp)
                            ) {
                                Text(
                                    text = config.autoZone,
                                    fontSize = 11.sp,
                                    color = MoonCyan,
                                    fontWeight = FontWeight.SemiBold
                                )
                            }
                        }*/
                    }
                }
            }

            // Session Stats Bar
            if (isRunning)
                BotSessionStatsBar(
                    stats = partyStats,
                    isRunning = isRunning,
                    botType = "Slavery Party",
                    accentColor = SlaveIndigo
                )

            // Start / Stop CTA Button
            Button(
                onClick = {
                    if (isRunning) {
                        onStopParty()
                    } else {
                        onStartParty()
                    }
                },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (isRunning) ErrorRed else SuccessGreen
                )
            ) {
                Icon(
                    imageVector = if (isRunning) Icons.Filled.Stop else Icons.Filled.PlayArrow,
                    contentDescription = null,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.size(8.dp))
                Text(
                    text = if (isRunning) "STOP PARTY" else "START PARTY",
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp
                )
            }

            // Real-time Monster HP
            val activeMonsters =
                telemetryMap.values.firstOrNull { it.running && it.monsters.isNotEmpty() }?.monsters
                    ?: emptyList()
            val activeCell =
                telemetryMap.values.firstOrNull { it.running && it.cell.isNotEmpty() && it.cell != "-" }?.cell
                    ?: ""

            AnimatedVisibility(
                visible = isRunning && activeMonsters.isNotEmpty(),
                enter = expandVertically() + fadeIn(),
                exit = shrinkVertically() + fadeOut()
            ) {
                MonsterTelemetryCard(
                    monsters = activeMonsters,
                    currentCell = activeCell
                )
            }

            // Slot Account ViewPager Tab Navigation
            ScrollableTabRow(
                selectedTabIndex = pagerState.currentPage,
                containerColor = Color(0xFF131522),
                contentColor = TextPrimary,
                edgePadding = 0.dp,
                indicator = { tabPositions ->
                    if (pagerState.currentPage < tabPositions.size) {
                        TabRowDefaults.SecondaryIndicator(
                            Modifier.tabIndicatorOffset(tabPositions[pagerState.currentPage]),
                            color = SlaveIndigo
                        )
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .border(1.dp, Color(0xFF2E3350), RoundedCornerShape(12.dp))
            ) {
                slotLabels.forEachIndexed { index, label ->
                    val slotKey = slotKeys[index]
                    val slotTel = telemetryMap[slotKey] ?: SlotTelemetry()
                    val slotConf = config.slots[slotKey] ?: SlaveSlotConfig()
                    val selected = pagerState.currentPage == index

                    Tab(
                        selected = selected,
                        onClick = {
                            coroutineScope.launch {
                                pagerState.animateScrollToPage(index)
                            }
                        },
                        text = {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                Box(
                                    modifier = Modifier
                                        .size(8.dp)
                                        .clip(CircleShape)
                                        .background(
                                            when {
                                                slotTel.running -> SuccessGreen
                                                slotConf.enabled -> SlaveIndigo
                                                else -> TextMuted
                                            }
                                        )
                                )
                                Text(
                                    text = label,
                                    fontSize = 12.sp,
                                    fontWeight = if (selected) FontWeight.Bold else FontWeight.Medium,
                                    color = if (selected) SlaveIndigo else TextSecondary
                                )
                            }
                        }
                    )
                }
            }

            // HorizontalPager for each Slot
            HorizontalPager(
                state = pagerState,
                modifier = Modifier.fillMaxWidth()
            ) { page ->
                val slotKey = slotKeys[page]
                val slotTitle = slotFullTitles[page]
                val slotConf = config.slots[slotKey] ?: SlaveSlotConfig()
                val slotTel = telemetryMap[slotKey] ?: SlotTelemetry()

                // Filter logs for this specific slot
                val slotUsername = slotConf.username.trim()
                val slotLogs = logs.filter { log ->
                    if (slotUsername.isNotEmpty()) {
                        log.username.equals(slotUsername, ignoreCase = true) || log.username.equals(
                            slotKey,
                            ignoreCase = true
                        )
                    } else {
                        log.username.equals(slotKey, ignoreCase = true)
                    }
                }

                Column(
                    modifier = Modifier.fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    // 1. Slave Slot Card
                    SlaveSlotCard(
                        slotKey = slotKey,
                        title = slotTitle,
                        config = slotConf,
                        telemetry = slotTel,
                        isPartyRunning = isRunning,
                        accentColor = SlaveIndigo,
                        onConfigChange = { onUpdateSlot(slotKey, it) }
                    )

                    // 2. Dedicated Log Console for this Slot
                    LiveLogConsole(
                        logs = slotLogs,
                        title = "Logs - Slot ${page + 1}${if (slotUsername.isNotEmpty()) " ($slotUsername)" else ""}",
                        onClearLogs = onClearLogs
                    )
                }
            }

            Spacer(modifier = Modifier.height(24.dp))
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SlaveSlotCard(
    modifier: Modifier = Modifier,
    slotKey: String,
    title: String,
    config: SlaveSlotConfig,
    telemetry: SlotTelemetry,
    isPartyRunning: Boolean,
    accentColor: Color = SlaveIndigo,
    onConfigChange: (SlaveSlotConfig) -> Unit
) {
    var passwordVisible by remember { mutableStateOf(false) }

    Card(
        modifier = modifier
            .fillMaxWidth()
            .border(
                1.dp,
                if (telemetry.running) SuccessGreen.copy(alpha = 0.5f) else Color(0xFF2E3350),
                RoundedCornerShape(16.dp)
            ),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = CardDark)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 8.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Header Row: Status, Title (with username when running), Enabled Switch, Class chip
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
                            .background(
                                when {
                                    telemetry.running -> SuccessGreen
                                    config.enabled -> accentColor
                                    else -> Color(0xFF64748B)
                                }
                            )
                    )
                    Text(
                        text = if (isPartyRunning && config.username.isNotEmpty()) "$title (${config.username})" else title,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = TextPrimary
                    )
                }

                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    if (config.charClass.isNotEmpty()) {
                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(6.dp))
                                .background(accentColor.copy(alpha = 0.15f))
                                .padding(horizontal = 8.dp, vertical = 3.dp)
                        ) {
                            Text(
                                text = config.charClass,
                                fontSize = 10.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = accentColor
                            )
                        }
                    }
                    if (telemetry.running) {
                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(6.dp))
                                .background(SuccessGreen.copy(alpha = 0.2f))
                                .padding(horizontal = 8.dp, vertical = 3.dp)
                        ) {
                            Text(
                                text = "ACTIVE",
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                color = SuccessGreen
                            )
                        }
                    }
                    if (!isPartyRunning) {
                        Switch(
                            checked = config.enabled,
                            onCheckedChange = { onConfigChange(config.copy(enabled = it)) },
                            enabled = true,
                            colors = SwitchDefaults.colors(
                                checkedThumbColor = Color.White,
                                checkedTrackColor = accentColor,
                                uncheckedThumbColor = Color(0xFF94A3B8),
                                uncheckedTrackColor = Color(0xFF334155)
                            )
                        )
                    }
                }
            }

            if (isPartyRunning) {
                // RUNNING MODE: Telemetry ONLY, non-telemetry fields are hidden
                if (!config.enabled) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(8.dp))
                            .background(Color(0xFF161928))
                            .padding(12.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "Slot is disabled (Not active in party)",
                            fontSize = 12.sp,
                            color = TextMuted
                        )
                    }
                } else if (telemetry.running) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(10.dp))
                            .background(Color(0xFF0F111A))
                            .padding(12.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        // Location: Map, Cell, Pad
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(
                                text = "Map: ${telemetry.map} (${telemetry.cell}, ${telemetry.pad})",
                                fontSize = 11.sp,
                                color = TextSecondary,
                                fontFamily = FontFamily.Monospace
                            )
                            Text(
                                text = if (telemetry.isConnected) "Connected" else "Connecting...",
                                fontSize = 11.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = if (telemetry.isConnected) SuccessGreen else SunGold
                            )
                        }

                        // Target Monsters
                        if (telemetry.targetMonsters.isNotEmpty()) {
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .clip(RoundedCornerShape(6.dp))
                                    .background(Color(0xFF161928))
                                    .padding(horizontal = 8.dp, vertical = 5.dp),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    text = "Target Monsters",
                                    fontSize = 11.sp,
                                    color = TextSecondary
                                )
                                Text(
                                    text = telemetry.targetMonsters,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = TextPrimary
                                )
                            }
                        }

                        // HP Bar
                        Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text(
                                    text = "HP",
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = ErrorRed
                                )
                                Text(
                                    text = "${telemetry.hp} / ${telemetry.maxHp}",
                                    fontSize = 10.sp,
                                    color = TextPrimary
                                )
                            }
                            val hpFraction =
                                if (telemetry.maxHp > 0) (telemetry.hp.toFloat() / telemetry.maxHp.toFloat()).coerceIn(
                                    0f,
                                    1f
                                ) else 0f
                            LinearProgressIndicator(
                                progress = { hpFraction },
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(6.dp)
                                    .clip(RoundedCornerShape(3.dp)),
                                color = ErrorRed,
                                trackColor = Color(0xFF2A1515)
                            )
                        }

                        // MP Bar
                        Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text(
                                    text = "MP",
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = MoonCyan
                                )
                                Text(
                                    text = "${telemetry.mp} / ${telemetry.maxMp}",
                                    fontSize = 10.sp,
                                    color = TextPrimary
                                )
                            }
                            val mpFraction =
                                if (telemetry.maxMp > 0) (telemetry.mp.toFloat() / telemetry.maxMp.toFloat()).coerceIn(
                                    0f,
                                    1f
                                ) else 0f
                            LinearProgressIndicator(
                                progress = { mpFraction },
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(6.dp)
                                    .clip(RoundedCornerShape(3.dp)),
                                color = MoonCyan,
                                trackColor = Color(0xFF0C242B)
                            )
                        }

                        // Skill Cooldowns
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            for (i in 0..5) {
                                val cd = telemetry.cooldowns[i] ?: 0.0
                                val isReady = cd <= 0.0
                                val isSoE = i == 5
                                val label = if (isSoE) "SoE" else "$i"

                                Column(
                                    horizontalAlignment = Alignment.CenterHorizontally,
                                    verticalArrangement = Arrangement.spacedBy(2.dp)
                                ) {
                                    Box(
                                        modifier = Modifier
                                            .size(32.dp)
                                            .clip(RoundedCornerShape(6.dp))
                                            .background(
                                                when {
                                                    !isReady -> Color(0xFF1E2130)
                                                    isSoE -> SunGold.copy(alpha = 0.25f)
                                                    else -> accentColor.copy(alpha = 0.2f)
                                                }
                                            )
                                            .border(
                                                1.dp,
                                                when {
                                                    !isReady -> Color(0xFF2E3350)
                                                    isSoE -> SunGold.copy(alpha = 0.6f)
                                                    else -> accentColor.copy(alpha = 0.5f)
                                                },
                                                RoundedCornerShape(6.dp)
                                            ),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        Text(
                                            text = if (isReady) label else String.format(
                                                java.util.Locale.US,
                                                "%.1f",
                                                cd
                                            ),
                                            fontSize = if (isReady) 11.sp else 9.sp,
                                            fontWeight = FontWeight.Bold,
                                            color = when {
                                                !isReady -> TextMuted
                                                isSoE -> SunGold
                                                else -> TextPrimary
                                            }
                                        )
                                    }
                                    Text(
                                        text = if (isSoE) "Taunt" else "S$i",
                                        fontSize = 8.sp,
                                        color = TextMuted
                                    )
                                }
                            }
                        }

                        // SoE Warning if active taunter but empty inventory
                        if (config.isTaunter) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    text = "Scroll of Enrage Qty: ${telemetry.soeQty}",
                                    fontSize = 11.sp,
                                    color = if (telemetry.soeQty > 0) SunGold else ErrorRed,
                                    fontWeight = FontWeight.SemiBold
                                )
                                if (telemetry.soeQty <= 0) {
                                    Row(
                                        verticalAlignment = Alignment.CenterVertically,
                                        horizontalArrangement = Arrangement.spacedBy(4.dp)
                                    ) {
                                        Icon(
                                            imageVector = Icons.Filled.Warning,
                                            contentDescription = null,
                                            tint = ErrorRed,
                                            modifier = Modifier.size(13.dp)
                                        )
                                        Text(
                                            text = "Missing Scroll!",
                                            fontSize = 11.sp,
                                            fontWeight = FontWeight.Bold,
                                            color = ErrorRed
                                        )
                                    }
                                }
                            }
                        }
                    }
                } else {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(8.dp))
                            .background(Color(0xFF161928))
                            .padding(16.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(10.dp)
                        ) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(16.dp),
                                strokeWidth = 2.dp,
                                color = accentColor
                            )
                            Text(
                                text = "Slot starting / waiting for connection...",
                                fontSize = 12.sp,
                                color = TextSecondary
                            )
                        }
                    }
                }
            } else {
                // EDIT MODE (Bot stopped): Show configuration inputs
                if (!config.enabled) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(8.dp))
                            .background(Color(0xFF161928))
                            .padding(12.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "This slot is currently disabled. Toggle the switch above to enable.",
                            fontSize = 12.sp,
                            color = TextMuted
                        )
                    }
                } else {
                    // Account Credentials
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        OutlinedTextField(
                            value = config.username,
                            onValueChange = { onConfigChange(config.copy(username = it)) },
                            label = { Text("Username") },
                            singleLine = true,
                            enabled = true,
                            modifier = Modifier.weight(1f),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = accentColor,
                                unfocusedBorderColor = Color(0xFF334155),
                                focusedTextColor = TextPrimary,
                                unfocusedTextColor = TextPrimary
                            )
                        )

                        OutlinedTextField(
                            value = config.password,
                            onValueChange = { onConfigChange(config.copy(password = it)) },
                            label = { Text("***", overflow = TextOverflow.Ellipsis) },
                            singleLine = true,
                            enabled = true,
                            visualTransformation = if (passwordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                            trailingIcon = {
                                IconButton(onClick = { passwordVisible = !passwordVisible }) {
                                    Icon(
                                        imageVector = if (passwordVisible) Icons.Filled.Visibility else Icons.Filled.VisibilityOff,
                                        contentDescription = "Toggle password visibility",
                                        tint = TextSecondary,
                                        modifier = Modifier.size(18.dp)
                                    )
                                }
                            },
                            modifier = Modifier.weight(1f),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = accentColor,
                                unfocusedBorderColor = Color(0xFF334155),
                                focusedTextColor = TextPrimary,
                                unfocusedTextColor = TextPrimary
                            )
                        )
                    }

                    // Character Class
                    OutlinedTextField(
                        value = config.charClass,
                        onValueChange = { onConfigChange(config.copy(charClass = it)) },
                        label = { Text("Class (e.g. Lord of Order, ArchPaladin)") },
                        singleLine = true,
                        enabled = true,
                        modifier = Modifier.fillMaxWidth(),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = accentColor,
                            unfocusedBorderColor = Color(0xFF334155),
                            focusedTextColor = TextPrimary,
                            unfocusedTextColor = TextPrimary
                        )
                    )

                    // Taunter Toggle
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(10.dp))
                            .background(Color(0xFF161928))
                            .padding(horizontal = 12.dp, vertical = 8.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = "Taunt Rotation (Scroll of Enrage)",
                                fontSize = 13.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = TextPrimary
                            )
                            Text(
                                text = "Rotation taunting",
                                fontSize = 11.sp,
                                color = TextSecondary
                            )
                        }
                        Switch(
                            checked = config.isTaunter,
                            onCheckedChange = { onConfigChange(config.copy(isTaunter = it)) },
                            enabled = true,
                            colors = SwitchDefaults.colors(
                                checkedThumbColor = Color.White,
                                checkedTrackColor = accentColor,
                                uncheckedThumbColor = Color(0xFF94A3B8),
                                uncheckedTrackColor = Color(0xFF334155)
                            )
                        )
                    }

                    // Combined Skill Rotation & Threshold Rules Section
                    CombinedCombatSkillsSection(
                        config = config,
                        isPartyRunning = false,
                        accentColor = accentColor,
                        onConfigChange = onConfigChange
                    )
                }
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Unified Combat Skills & Threshold Rules (Object Model)
// ---------------------------------------------------------------------------
@Composable
private fun CombinedCombatSkillsSection(
    config: SlaveSlotConfig,
    isPartyRunning: Boolean,
    accentColor: Color,
    onConfigChange: (SlaveSlotConfig) -> Unit
) {
    var skillToEdit by remember { mutableStateOf<Skill?>(null) }
    var editStepIndex by remember { mutableStateOf<Int?>(null) }
    var showAddDialog by remember { mutableStateOf(false) }

    val skills = config.skills

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, Color(0xFF2E3350), RoundedCornerShape(12.dp)),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF131522))
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            // Header Row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Icon(
                        imageVector = Icons.Filled.Bolt,
                        contentDescription = null,
                        tint = accentColor,
                        modifier = Modifier.size(16.dp)
                    )
                    Text(
                        text = "Combat Skills Rotation",
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Bold,
                        color = TextPrimary
                    )
                }

                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(6.dp))
                            .background(accentColor.copy(alpha = 0.15f))
                            .padding(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Text(
                            text = "${skills.size} Steps",
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            color = accentColor
                        )
                    }

                    if (skills.isNotEmpty() && !isPartyRunning) {
                        TextButton(
                            onClick = { onConfigChange(config.copy(skills = emptyList())) },
                            contentPadding = PaddingValues(horizontal = 6.dp, vertical = 2.dp),
                            modifier = Modifier.height(24.dp)
                        ) {
                            Text("Clear", fontSize = 11.sp, color = Color(0xFFEF4444))
                        }
                    }
                }
            }

            Text(
                text = "Skills will execute in order from top to bottom, looping back to the start. Drag ≡ handle to reorder.",
                fontSize = 11.sp,
                color = TextSecondary,
                lineHeight = 14.sp
            )

            // Reorderable Vertical List
            if (skills.isEmpty()) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(Color(0xFF0D0F18))
                        .border(1.dp, Color(0xFF262B45), RoundedCornerShape(8.dp))
                        .padding(vertical = 16.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "No skills in rotation. Tap '+ Add Skill' below.",
                        fontSize = 11.sp,
                        color = TextMuted
                    )
                }
            } else {
                ReorderableColumn(
                    list = skills,
                    onSettle = { fromIndex, toIndex ->
                        val updated = skills.toMutableList()
                        val item = updated.removeAt(fromIndex)
                        updated.add(toIndex, item)
                        onConfigChange(config.copy(skills = updated))
                    },
                    verticalArrangement = Arrangement.spacedBy(6.dp),
                    modifier = Modifier.fillMaxWidth()
                ) { index, skillItem, isDragging ->
                    key(skillItem.id) {
                        SkillVerticalItem(
                            stepIndex = index + 1,
                            skill = skillItem,
                            accentColor = accentColor,
                            isDragging = isDragging,
                            enabled = !isPartyRunning,
                            dragHandleModifier = Modifier.draggableHandle(enabled = !isPartyRunning),
                            onClick = {
                                if (!isPartyRunning) {
                                    skillToEdit = skillItem
                                    editStepIndex = index + 1
                                }
                            },
                            onRemove = {
                                val updated = skills.toMutableList().apply { removeAt(index) }
                                onConfigChange(config.copy(skills = updated))
                            }
                        )
                    }
                }
            }

            // Add Skill Button (Prominent dialog-only trigger)
            Button(
                onClick = { showAddDialog = true },
                enabled = !isPartyRunning,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(38.dp),
                shape = RoundedCornerShape(8.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF1E2438),
                    contentColor = Color.White
                ),
                border = BorderStroke(1.dp, accentColor.copy(alpha = 0.6f))
            ) {
                Icon(
                    imageVector = Icons.Filled.Add,
                    contentDescription = null,
                    modifier = Modifier.size(16.dp),
                    tint = accentColor
                )
                Spacer(Modifier.width(6.dp))
                Text(
                    text = "Add Skill",
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
            }
        }
    }

    // Dialog for Adding New Skill
    if (showAddDialog) {
        SkillEditorDialog(
            initialSkill = null,
            stepIndex = skills.size + 1,
            accentColor = accentColor,
            onDismiss = { showAddDialog = false },
            onConfirm = { newSkill ->
                onConfigChange(config.copy(skills = skills + newSkill))
                showAddDialog = false
            }
        )
    }

    // Dialog for Editing Existing Skill
    skillToEdit?.let { currentSkill ->
        SkillEditorDialog(
            initialSkill = currentSkill,
            stepIndex = editStepIndex ?: 1,
            accentColor = accentColor,
            onDismiss = {
                skillToEdit = null
                editStepIndex = null
            },
            onConfirm = { updatedSkill ->
                val updatedList = skills.map { if (it.id == currentSkill.id) updatedSkill else it }
                onConfigChange(config.copy(skills = updatedList))
                skillToEdit = null
                editStepIndex = null
            }
        )
    }
}

// ---------------------------------------------------------------------------
// Skill Vertical Item with Drag Handle & Reorderable styling
// ---------------------------------------------------------------------------
@Composable
private fun SkillVerticalItem(
    stepIndex: Int,
    skill: Skill,
    accentColor: Color,
    isDragging: Boolean,
    enabled: Boolean,
    dragHandleModifier: Modifier,
    onClick: () -> Unit,
    onRemove: () -> Unit
) {
    val borderColor = when {
        isDragging -> accentColor
        skill.thresholdType == ThresholdType.HP -> Color(0xFFEF4444).copy(alpha = 0.6f)
        skill.thresholdType == ThresholdType.MP -> Color(0xFF06B6D4).copy(alpha = 0.6f)
        else -> Color(0xFF2E3550)
    }
    val cardBg = if (isDragging) Color(0xFF222842) else Color(0xFF161A29)

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(10.dp))
            .background(cardBg)
            .border(
                width = if (isDragging) 1.5.dp else 1.dp,
                color = borderColor,
                shape = RoundedCornerShape(10.dp)
            )
            .clickable(enabled = enabled) { onClick() }
            .padding(horizontal = 8.dp, vertical = 6.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            // Left part: Drag Handle + Step Index + Skill Badge + Threshold Badge
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                modifier = Modifier.weight(1f)
            ) {
                // Drag handle
                Box(
                    modifier = Modifier
                        .size(30.dp)
                        .clip(RoundedCornerShape(6.dp))
                        .background(
                            if (isDragging) accentColor.copy(alpha = 0.25f) else Color(
                                0xFF1E2235
                            )
                        )
                        .then(dragHandleModifier),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Filled.DragHandle,
                        contentDescription = "Drag to reorder",
                        tint = if (isDragging) Color.White else TextMuted,
                        modifier = Modifier.size(18.dp)
                    )
                }

                // Step #
                Text(
                    text = "#$stepIndex",
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    color = TextMuted,
                    modifier = Modifier.width(22.dp)
                )

                // Skill Badge
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(6.dp))
                        .background(Color(0xFF222944))
                        .padding(horizontal = 8.dp, vertical = 4.dp)
                ) {
                    Text(
                        text = if (skill.index == 5) "Skill 5 (Taunt)" else "Skill ${skill.index}",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                }

                // Condition Badge
                when (skill.thresholdType) {
                    ThresholdType.HP -> {
                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(6.dp))
                                .background(Color(0xFFEF4444).copy(alpha = 0.18f))
                                .border(
                                    0.5.dp,
                                    Color(0xFFEF4444).copy(alpha = 0.4f),
                                    RoundedCornerShape(6.dp)
                                )
                                .padding(horizontal = 6.dp, vertical = 3.dp)
                        ) {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(3.dp)
                            ) {
                                Icon(
                                    imageVector = Icons.Filled.Favorite,
                                    contentDescription = null,
                                    tint = Color(0xFFEF4444),
                                    modifier = Modifier.size(10.dp)
                                )
                                Text(
                                    text = "HP ${skill.operator} ${skill.thresholdValue}%",
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = Color(0xFFFCA5A5)
                                )
                            }
                        }
                    }

                    ThresholdType.MP -> {
                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(6.dp))
                                .background(Color(0xFF06B6D4).copy(alpha = 0.18f))
                                .border(
                                    0.5.dp,
                                    Color(0xFF06B6D4).copy(alpha = 0.4f),
                                    RoundedCornerShape(6.dp)
                                )
                                .padding(horizontal = 6.dp, vertical = 3.dp)
                        ) {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(3.dp)
                            ) {
                                Icon(
                                    imageVector = Icons.Filled.WaterDrop,
                                    contentDescription = null,
                                    tint = Color(0xFF06B6D4),
                                    modifier = Modifier.size(10.dp)
                                )
                                Text(
                                    text = "MP ${skill.operator} ${skill.thresholdValue}%",
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = Color(0xFF67E8F9)
                                )
                            }
                        }
                    }

                    ThresholdType.NONE -> {
                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(6.dp))
                                .background(Color(0xFF282F48).copy(alpha = 0.5f))
                                .padding(horizontal = 6.dp, vertical = 3.dp)
                        ) {
                            Text(
                                text = "Always",
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Normal,
                                color = Color(0xFF94A3B8)
                            )
                        }
                    }
                }
            }

            // Right part: Action buttons (Edit & Delete)
            if (enabled) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(2.dp)
                ) {
                    IconButton(
                        onClick = onClick,
                        modifier = Modifier.size(28.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Filled.Edit,
                            contentDescription = "Edit Condition",
                            tint = Color(0xFF94A3B8),
                            modifier = Modifier.size(14.dp)
                        )
                    }

                    IconButton(
                        onClick = onRemove,
                        modifier = Modifier.size(28.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Filled.Close,
                            contentDescription = "Remove Skill",
                            tint = ErrorRed.copy(alpha = 0.8f),
                            modifier = Modifier.size(14.dp)
                        )
                    }
                }
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Skill Editor Dialog (Add & Edit Skill with Condition, Presets Removed)
// ---------------------------------------------------------------------------
@Composable
private fun SkillEditorDialog(
    initialSkill: Skill?,
    stepIndex: Int,
    accentColor: Color,
    onDismiss: () -> Unit,
    onConfirm: (Skill) -> Unit
) {
    val isEditing = initialSkill != null
    var selectedIndex by remember { mutableStateOf(initialSkill?.index ?: 1) }
    var selectedThresholdType by remember {
        mutableStateOf(
            initialSkill?.thresholdType ?: ThresholdType.NONE
        )
    }
    var selectedOperator by remember { mutableStateOf(initialSkill?.operator ?: "<") }
    var selectedThresholdValue by remember {
        mutableStateOf(if (initialSkill != null && initialSkill.thresholdValue > 0) initialSkill.thresholdValue else 50)
    }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Column {
                Text(
                    text = if (isEditing) "Edit Skill #$stepIndex" else "Add Skill",
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
                Text(
                    text = if (isEditing) "Modify skill number or trigger condition" else "Select skill number and optional HP/MP condition",
                    fontSize = 12.sp,
                    color = TextSecondary
                )
            }
        },
        text = {
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                // 1. Skill Index Selector
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(
                        text = "Skill Number:",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = TextSecondary
                    )

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(6.dp)
                    ) {
                        (1..5).forEach { num ->
                            val isSelected = selectedIndex == num
                            Box(
                                modifier = Modifier
                                    .weight(1f)
                                    .clip(RoundedCornerShape(8.dp))
                                    .background(
                                        if (isSelected) accentColor.copy(alpha = 0.25f) else Color(
                                            0xFF1E2235
                                        )
                                    )
                                    .border(
                                        1.dp,
                                        if (isSelected) accentColor else Color(0xFF333B58),
                                        RoundedCornerShape(8.dp)
                                    )
                                    .clickable { selectedIndex = num }
                                    .padding(vertical = 8.dp),
                                contentAlignment = Alignment.Center
                            ) {
                                Text(
                                    text = if (num == 5) "S5" else "S$num",
                                    fontSize = 12.sp,
                                    fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                                    color = if (isSelected) Color.White else TextSecondary
                                )
                            }
                        }
                    }
                }

                // 2. Threshold Condition Type
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(
                        text = "Cast Trigger Condition:",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = TextSecondary
                    )

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(6.dp)
                    ) {
                        // NONE (Always)
                        val isNone = selectedThresholdType == ThresholdType.NONE
                        Box(
                            modifier = Modifier
                                .weight(1f)
                                .clip(RoundedCornerShape(8.dp))
                                .background(
                                    if (isNone) Color(0xFF3B4368).copy(alpha = 0.4f) else Color(
                                        0xFF1A1F30
                                    )
                                )
                                .border(
                                    1.dp,
                                    if (isNone) Color(0xFF94A3B8) else Color(0xFF2E3550),
                                    RoundedCornerShape(8.dp)
                                )
                                .clickable { selectedThresholdType = ThresholdType.NONE }
                                .padding(vertical = 8.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = "Always",
                                fontSize = 11.sp,
                                fontWeight = if (isNone) FontWeight.Bold else FontWeight.Normal,
                                color = if (isNone) Color.White else TextSecondary
                            )
                        }

                        // HP
                        val isHp = selectedThresholdType == ThresholdType.HP
                        Box(
                            modifier = Modifier
                                .weight(1f)
                                .clip(RoundedCornerShape(8.dp))
                                .background(
                                    if (isHp) Color(0xFFEF4444).copy(alpha = 0.25f) else Color(
                                        0xFF1A1F30
                                    )
                                )
                                .border(
                                    1.dp,
                                    if (isHp) Color(0xFFEF4444) else Color(0xFF2E3550),
                                    RoundedCornerShape(8.dp)
                                )
                                .clickable { selectedThresholdType = ThresholdType.HP }
                                .padding(vertical = 8.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(4.dp)
                            ) {
                                Icon(
                                    imageVector = Icons.Filled.Favorite,
                                    contentDescription = null,
                                    tint = if (isHp) Color(0xFFEF4444) else TextMuted,
                                    modifier = Modifier.size(12.dp)
                                )
                                Text(
                                    text = "HP",
                                    fontSize = 11.sp,
                                    fontWeight = if (isHp) FontWeight.Bold else FontWeight.Normal,
                                    color = if (isHp) Color.White else TextSecondary
                                )
                            }
                        }

                        // MP
                        val isMp = selectedThresholdType == ThresholdType.MP
                        Box(
                            modifier = Modifier
                                .weight(1f)
                                .clip(RoundedCornerShape(8.dp))
                                .background(
                                    if (isMp) Color(0xFF06B6D4).copy(alpha = 0.25f) else Color(
                                        0xFF1A1F30
                                    )
                                )
                                .border(
                                    1.dp,
                                    if (isMp) Color(0xFF06B6D4) else Color(0xFF2E3550),
                                    RoundedCornerShape(8.dp)
                                )
                                .clickable { selectedThresholdType = ThresholdType.MP }
                                .padding(vertical = 8.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(4.dp)
                            ) {
                                Icon(
                                    imageVector = Icons.Filled.WaterDrop,
                                    contentDescription = null,
                                    tint = if (isMp) Color(0xFF06B6D4) else TextMuted,
                                    modifier = Modifier.size(12.dp)
                                )
                                Text(
                                    text = "MP",
                                    fontSize = 11.sp,
                                    fontWeight = if (isMp) FontWeight.Bold else FontWeight.Normal,
                                    color = if (isMp) Color.White else TextSecondary
                                )
                            }
                        }
                    }
                }

                // 3. Condition Details (if HP or MP selected)
                AnimatedVisibility(
                    visible = selectedThresholdType != ThresholdType.NONE,
                    enter = expandVertically() + fadeIn(),
                    exit = shrinkVertically() + fadeOut()
                ) {
                    val activeColor =
                        if (selectedThresholdType == ThresholdType.HP) Color(0xFFEF4444) else Color(
                            0xFF06B6D4
                        )
                    val cardBg =
                        if (selectedThresholdType == ThresholdType.HP) Color(0xFF1C1318) else Color(
                            0xFF101B26
                        )
                    val cardBorder =
                        if (selectedThresholdType == ThresholdType.HP) Color(0xFF4A1F29) else Color(
                            0xFF1E3A52
                        )

                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(10.dp))
                            .background(cardBg)
                            .border(1.dp, cardBorder, RoundedCornerShape(10.dp))
                            .padding(10.dp)
                    ) {
                        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            // Operator
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(8.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    text = "Operator:",
                                    fontSize = 11.sp,
                                    color = TextSecondary,
                                    modifier = Modifier.width(60.dp)
                                )

                                val isBelow = selectedOperator == "<"
                                Box(
                                    modifier = Modifier
                                        .weight(1f)
                                        .clip(RoundedCornerShape(6.dp))
                                        .background(
                                            if (isBelow) activeColor.copy(alpha = 0.25f) else Color(
                                                0xFF1E2235
                                            )
                                        )
                                        .border(
                                            1.dp,
                                            if (isBelow) activeColor else Color(0xFF333B58),
                                            RoundedCornerShape(6.dp)
                                        )
                                        .clickable { selectedOperator = "<" }
                                        .padding(vertical = 5.dp),
                                    contentAlignment = Alignment.Center
                                ) {
                                    Text(
                                        text = "Below (<)",
                                        fontSize = 11.sp,
                                        fontWeight = if (isBelow) FontWeight.Bold else FontWeight.Normal,
                                        color = if (isBelow) Color.White else TextSecondary
                                    )
                                }

                                val isAbove = selectedOperator == ">"
                                Box(
                                    modifier = Modifier
                                        .weight(1f)
                                        .clip(RoundedCornerShape(6.dp))
                                        .background(
                                            if (isAbove) activeColor.copy(alpha = 0.25f) else Color(
                                                0xFF1E2235
                                            )
                                        )
                                        .border(
                                            1.dp,
                                            if (isAbove) activeColor else Color(0xFF333B58),
                                            RoundedCornerShape(6.dp)
                                        )
                                        .clickable { selectedOperator = ">" }
                                        .padding(vertical = 5.dp),
                                    contentAlignment = Alignment.Center
                                ) {
                                    Text(
                                        text = "Above (>)",
                                        fontSize = 11.sp,
                                        fontWeight = if (isAbove) FontWeight.Bold else FontWeight.Normal,
                                        color = if (isAbove) Color.White else TextSecondary
                                    )
                                }
                            }

                            // Slider
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    text = "${selectedThresholdType.name} Trigger Level:",
                                    fontSize = 11.sp,
                                    color = TextSecondary
                                )
                                Text(
                                    text = "$selectedThresholdValue%",
                                    fontSize = 13.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = activeColor
                                )
                            }

                            Slider(
                                value = selectedThresholdValue.coerceIn(5, 95).toFloat(),
                                onValueChange = { selectedThresholdValue = it.toInt() },
                                valueRange = 5f..95f,
                                steps = 17,
                                colors = SliderDefaults.colors(
                                    thumbColor = activeColor,
                                    activeTrackColor = activeColor,
                                    inactiveTrackColor = Color(0xFF333B58)
                                ),
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(24.dp)
                            )

                            // Plain text preview
                            val condText = if (selectedOperator == "<") "below" else "above"
                            Text(
                                text = "💡 Cast Skill $selectedIndex ONLY when ${selectedThresholdType.name} is $condText $selectedThresholdValue%.",
                                fontSize = 10.sp,
                                color = Color(0xFFCBD5E1)
                            )
                        }
                    }
                }
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    val skill = Skill(
                        id = initialSkill?.id ?: java.util.UUID.randomUUID().toString(),
                        index = selectedIndex,
                        thresholdType = selectedThresholdType,
                        operator = selectedOperator,
                        thresholdValue = if (selectedThresholdType == ThresholdType.NONE) 0 else selectedThresholdValue
                    )
                    onConfirm(skill)
                },
                colors = ButtonDefaults.buttonColors(containerColor = accentColor)
            ) {
                Text(if (isEditing) "Save Changes" else "Add to Rotation", color = Color.White)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel", color = TextSecondary)
            }
        },
        containerColor = Color(0xFF161928),
        shape = RoundedCornerShape(14.dp)
    )
}

@Preview(showBackground = true, backgroundColor = 0xFF0B0D14)
@Composable
private fun SlaveryContentIdlePreview() {
    MyApplicationTheme {
        SlaveryContent(
            config = SlaveryConfig(
                server = "Gravelyn",
                followPlayer = "MasterPlayer",
                defaultRoomNumber = 9099,
                copyWalk = true,
                autoZone = "none",
                targetsPriority = "Defense Drone,Staff of Inversion",
                slots = mapOf(
                    "slot1" to SlaveSlotConfig(
                        enabled = true,
                        username = "Slave1",
                        charClass = "Lord of Order",
                        skills = listOf(
                            Skill(index = 1),
                            Skill(
                                index = 2,
                                thresholdType = ThresholdType.HP,
                                operator = "<",
                                thresholdValue = 50
                            ),
                            Skill(index = 3),
                            Skill(
                                index = 4,
                                thresholdType = ThresholdType.MP,
                                operator = ">",
                                thresholdValue = 30
                            )
                        ),
                        isTaunter = true
                    ),
                    "slot2" to SlaveSlotConfig(
                        enabled = true,
                        username = "Slave2",
                        charClass = "Legion Revenant",
                        skills = listOf(
                            Skill(index = 1),
                            Skill(index = 2),
                            Skill(index = 3),
                            Skill(index = 4)
                        )
                    ),
                    "slot3" to SlaveSlotConfig(
                        enabled = false,
                        username = "Slave3",
                        charClass = "ArchPaladin",
                        skills = listOf(
                            Skill(index = 1),
                            Skill(index = 2),
                            Skill(index = 3),
                            Skill(index = 4)
                        )
                    ),
                    "slot4" to SlaveSlotConfig(
                        enabled = false,
                        username = "Slave4",
                        charClass = "StoneCrusher",
                        skills = listOf(
                            Skill(index = 1),
                            Skill(index = 2),
                            Skill(index = 3),
                            Skill(index = 4)
                        )
                    )
                )
            ),
            telemetryMap = emptyMap(),
            partyStats = PartyStats(),
            logs = emptyList(),
            isRunning = false,
            onBack = {},
            onOpenSettings = {},
            onUpdateSlot = { _, _ -> },
            onStartParty = {},
            onStopParty = {},
            onClearLogs = {}
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF0B0D14)
@Composable
private fun SlaveryContentActivePreview() {
    MyApplicationTheme {
        SlaveryContent(
            config = SlaveryConfig(
                server = "Gravelyn",
                followPlayer = "MasterPlayer",
                defaultRoomNumber = 9099,
                copyWalk = true,
                autoZone = "Astral Empyrean",
                targetsPriority = "Defense Drone,Staff of Inversion",
                slots = mapOf(
                    "slot1" to SlaveSlotConfig(
                        enabled = true,
                        username = "Slave1",
                        charClass = "Lord of Order",
                        skills = listOf(
                            Skill(index = 1),
                            Skill(
                                index = 2,
                                thresholdType = ThresholdType.HP,
                                operator = "<",
                                thresholdValue = 50
                            ),
                            Skill(index = 3),
                            Skill(index = 4)
                        ),
                        isTaunter = true
                    ),
                    "slot2" to SlaveSlotConfig(
                        enabled = true,
                        username = "Slave2",
                        charClass = "Legion Revenant",
                        skills = listOf(
                            Skill(index = 1),
                            Skill(index = 2),
                            Skill(index = 3),
                            Skill(index = 4)
                        )
                    ),
                    "slot3" to SlaveSlotConfig(
                        enabled = false,
                        username = "Slave3",
                        charClass = "ArchPaladin",
                        skills = listOf(
                            Skill(index = 1),
                            Skill(index = 2),
                            Skill(index = 3),
                            Skill(index = 4)
                        )
                    ),
                    "slot4" to SlaveSlotConfig(
                        enabled = false,
                        username = "Slave4",
                        charClass = "StoneCrusher",
                        skills = listOf(
                            Skill(index = 1),
                            Skill(index = 2),
                            Skill(index = 3),
                            Skill(index = 4)
                        )
                    )
                )
            ),
            telemetryMap = mapOf(
                "slot1" to SlotTelemetry(
                    running = true,
                    isConnected = true,
                    map = "astralempyrean",
                    cell = "Boss",
                    pad = "Left",
                    hp = 2850,
                    maxHp = 3000,
                    mp = 180,
                    maxMp = 200,
                    soeQty = 45,
                    targetMonsters = "Defense Drone",
                    cooldowns = mapOf(0 to 0.0, 1 to 1.2, 2 to 0.0, 3 to 3.5, 4 to 0.0, 5 to 5.1),
                    monsters = listOf(
                        MonsterTelemetry(
                            monMapId = "1",
                            monName = "Defense Drone",
                            hp = 145000,
                            maxHp = 500000,
                            isAlive = true
                        ),
                        MonsterTelemetry(
                            monMapId = "2",
                            monName = "Staff of Inversion",
                            hp = 0,
                            maxHp = 250000,
                            isAlive = false
                        )
                    )
                ),
                "slot2" to SlotTelemetry(
                    running = true,
                    isConnected = true,
                    map = "astralempyrean",
                    cell = "Boss",
                    pad = "Left",
                    hp = 2400,
                    maxHp = 2500,
                    mp = 90,
                    maxMp = 100,
                    targetMonsters = "Defense Drone"
                )
            ),
            partyStats = PartyStats(timeRunning = 425L, clearedCount = 8),
            logs = listOf(
                LogEntry(
                    botType = "slavery",
                    username = "Slave1",
                    message = "[Slave1] Moving to master position (Boss, Left)"
                ),
                LogEntry(
                    botType = "slavery",
                    username = "Slave1",
                    message = "[Slave1] Casting skill 2 [Healing Light]"
                ),
                LogEntry(
                    botType = "slavery",
                    username = "Slave2",
                    message = "[Slave2] Attacking Defense Drone with Skill 1"
                )
            ),
            isRunning = true,
            onBack = {},
            onOpenSettings = {},
            onUpdateSlot = { _, _ -> },
            onStartParty = {},
            onStopParty = {},
            onClearLogs = {}
        )
    }
}
