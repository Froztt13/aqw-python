package froztt13.python.aqw.ui.screens

import android.Manifest
import android.os.Build
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.ScrollableTabRow
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRowDefaults
import androidx.compose.material3.TabRowDefaults.tabIndicatorOffset
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import froztt13.python.aqw.data.EclipseConfig
import froztt13.python.aqw.data.LogEntry
import froztt13.python.aqw.data.MonsterTelemetry
import froztt13.python.aqw.data.PartyStats
import froztt13.python.aqw.data.SlotConfig
import froztt13.python.aqw.data.SlotTelemetry
import froztt13.python.aqw.helper.BatteryOptimizationHelper
import froztt13.python.aqw.service.BotForegroundService
import froztt13.python.aqw.ui.components.BotSessionStatsBar
import froztt13.python.aqw.ui.components.LiveLogConsole
import froztt13.python.aqw.ui.components.MonsterTelemetryCard
import froztt13.python.aqw.ui.components.ServerDropdown
import froztt13.python.aqw.ui.components.SlotCard
import froztt13.python.aqw.ui.theme.BgDark
import froztt13.python.aqw.ui.theme.CardDark
import froztt13.python.aqw.ui.theme.EclipseMagenta
import froztt13.python.aqw.ui.theme.ErrorRed
import froztt13.python.aqw.ui.theme.MyApplicationTheme
import froztt13.python.aqw.ui.theme.SuccessGreen
import froztt13.python.aqw.ui.theme.TextMuted
import froztt13.python.aqw.ui.theme.TextPrimary
import froztt13.python.aqw.ui.theme.TextSecondary
import froztt13.python.aqw.viewmodel.EclipseViewModel
import kotlinx.coroutines.launch

@Composable
fun EclipseScreen(
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: EclipseViewModel = viewModel()
) {
    val context = LocalContext.current
    val config by viewModel.eclipseConfig.collectAsState()
    val telemetryMap by viewModel.eclipseStatus.collectAsState()
    val partyStats by viewModel.partyStats.collectAsState()
    val logs by viewModel.eclipseLogs.collectAsState()
    val isRunning by viewModel.isRunning.collectAsState()

    val notifPermissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { /* Permission result handled */ }

    EclipseContent(
        config = config,
        telemetryMap = telemetryMap,
        partyStats = partyStats,
        logs = logs,
        isRunning = isRunning,
        onBack = onBack,
        onUpdateSettings = { server, room ->
            viewModel.updateEclipseSettings(server, room)
        },
        onUpdateSlot = { slotKey, slotConfig ->
            viewModel.updateEclipseSlot(slotKey, slotConfig)
        },
        onResetSettings = {
            viewModel.resetEclipseConfig()
        },
        onStartParty = {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
                !BatteryOptimizationHelper.hasNotificationPermission(context)
            ) {
                notifPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
            viewModel.startEclipse { success, error ->
                if (success) {
                    BotForegroundService.start(
                        context = context,
                        botTitle = "Maid Eclipse Bot",
                        botSubtitle = "Eclipse Shrine active"
                    )
                } else if (error != null) {
                    Toast.makeText(context, error, Toast.LENGTH_LONG).show()
                }
            }
        },
        onStopParty = {
            viewModel.stopEclipse()
            BotForegroundService.stop(context)
        },
        onClearLogs = { viewModel.clearLogs("eclipse") },
        modifier = modifier
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EclipseContent(
    modifier: Modifier = Modifier,
    config: EclipseConfig,
    telemetryMap: Map<String, SlotTelemetry>,
    partyStats: PartyStats = PartyStats(),
    logs: List<LogEntry>,
    isRunning: Boolean,
    onBack: () -> Unit,
    onUpdateSettings: (server: String, roomNumber: Int) -> Unit,
    onUpdateSlot: (slotKey: String, slotConfig: SlotConfig) -> Unit,
    onResetSettings: () -> Unit = {},
    onStartParty: () -> Unit,
    onStopParty: () -> Unit,
    onClearLogs: () -> Unit
) {
    val coroutineScope = rememberCoroutineScope()
    val scrollState = rememberScrollState()
    var showSettings by remember { mutableStateOf(false) }
    var showResetConfirmDialog by remember { mutableStateOf(false) }

    var showPasswordDialog by remember { mutableStateOf(false) }
    var passwordInput by remember { mutableStateOf("") }
    var passwordError by remember { mutableStateOf(false) }
    var passwordVisible by remember { mutableStateOf(false) }

    val themeColor = EclipseMagenta

    val slotKeys = listOf("slot1", "slot2", "slot3", "slot4")
    val slotLabels = listOf("Slot 1", "Slot 2", "Slot 3", "Slot 4")
    val slotFullTitles = listOf(
        "Slot 1",
        "Slot 2",
        "Slot 3",
        "Slot 4"
    )

    val pagerState = rememberPagerState(initialPage = 0) { 4 }

    Scaffold(
        modifier = modifier.fillMaxSize(),
        containerColor = BgDark,
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "Maid Eclipse Client",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = TextPrimary
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Back",
                            tint = TextPrimary
                        )
                    }
                },
                actions = {
                    // Settings Toggle Button
                    IconButton(
                        onClick = { showSettings = !showSettings },
                        modifier = Modifier
                            .padding(end = 4.dp)
                            .clip(RoundedCornerShape(8.dp))
                            .background(if (showSettings) themeColor.copy(alpha = 0.2f) else Color.Transparent)
                    ) {
                        Icon(
                            imageVector = Icons.Filled.Settings,
                            contentDescription = "Toggle Settings",
                            tint = if (showSettings) themeColor else TextSecondary
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
                .padding(horizontal = 16.dp, vertical = 8.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            // Hideable Global Settings Card
            AnimatedVisibility(
                visible = showSettings,
                enter = expandVertically() + fadeIn(),
                exit = shrinkVertically() + fadeOut()
            ) {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .border(1.dp, themeColor.copy(alpha = 0.4f), RoundedCornerShape(16.dp)),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = CardDark)
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = "Global Session Settings",
                                fontSize = 13.sp,
                                fontWeight = FontWeight.Bold,
                                color = themeColor
                            )
                            Text(
                                text = "Tap gear icon to hide",
                                fontSize = 10.sp,
                                color = TextMuted
                            )
                        }

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(10.dp)
                        ) {
                            ServerDropdown(
                                selectedServer = config.server,
                                enabled = !isRunning,
                                onServerSelected = { onUpdateSettings(it, config.roomNumber) },
                                modifier = Modifier.weight(1f)
                            )

                            OutlinedTextField(
                                value = config.roomNumber.toString(),
                                onValueChange = {
                                    val num = it.toIntOrNull() ?: 1
                                    onUpdateSettings(config.server, num)
                                },
                                label = { Text("Room #") },
                                singleLine = true,
                                enabled = !isRunning,
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                                modifier = Modifier.weight(1f),
                                colors = OutlinedTextFieldDefaults.colors(
                                    focusedBorderColor = themeColor,
                                    unfocusedBorderColor = Color(0xFF334155),
                                    focusedTextColor = TextPrimary,
                                    unfocusedTextColor = TextPrimary
                                )
                            )
                        }

                        // Reset Settings Button
                        OutlinedButton(
                            onClick = { showResetConfirmDialog = true },
                            enabled = !isRunning,
                            shape = RoundedCornerShape(10.dp),
                            modifier = Modifier.fillMaxWidth(),
                            border = BorderStroke(1.dp, ErrorRed.copy(alpha = 0.5f)),
                            colors = ButtonDefaults.outlinedButtonColors(
                                contentColor = ErrorRed
                            )
                        ) {
                            Icon(
                                imageVector = Icons.Filled.Refresh,
                                contentDescription = "Reset Settings",
                                modifier = Modifier.size(16.dp)
                            )
                            Spacer(modifier = Modifier.size(8.dp))
                            Text(
                                text = "Reset Settings to Default",
                                fontSize = 12.sp,
                                fontWeight = FontWeight.SemiBold
                            )
                        }
                    }
                }
            }

            // Reset Confirmation Dialog
            if (showResetConfirmDialog) {
                AlertDialog(
                    onDismissRequest = { showResetConfirmDialog = false },
                    icon = {
                        Icon(
                            imageVector = Icons.Filled.Warning,
                            contentDescription = "Reset Confirmation",
                            tint = ErrorRed,
                            modifier = Modifier.size(28.dp)
                        )
                    },
                    title = {
                        Text(
                            text = "Reset to Default Settings?",
                            fontWeight = FontWeight.Bold,
                            color = TextPrimary
                        )
                    },
                    text = {
                        Text(
                            text = "This will restore all session settings and slot configurations to their original default presets. Are you sure you want to proceed?",
                            color = TextSecondary,
                            fontSize = 13.sp
                        )
                    },
                    confirmButton = {
                        Button(
                            onClick = {
                                onResetSettings()
                                showResetConfirmDialog = false
                            },
                            colors = ButtonDefaults.buttonColors(containerColor = ErrorRed)
                        ) {
                            Text("Reset", color = Color.White, fontWeight = FontWeight.Bold)
                        }
                    },
                    dismissButton = {
                        TextButton(onClick = { showResetConfirmDialog = false }) {
                            Text("Cancel", color = TextMuted)
                        }
                    },
                    containerColor = CardDark,
                    shape = RoundedCornerShape(16.dp)
                )
            }

            // Session Summary: Time Running & Cleared Loops
            BotSessionStatsBar(
                stats = partyStats,
                isRunning = isRunning,
                botType = "Maid Eclipse",
                accentColor = themeColor
            )

            // Start / Stop CTA Button
            Button(
                onClick = {
                    if (isRunning) {
                        onStopParty()
                    } else {
                        passwordInput = ""
                        passwordError = false
                        passwordVisible = false
                        showPasswordDialog = true
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
                    text = if (isRunning) "STOP" else "START",
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp
                )
            }

            // Password Confirmation Dialog to Start Bot
            if (showPasswordDialog) {
                AlertDialog(
                    onDismissRequest = {
                        showPasswordDialog = false
                        passwordInput = ""
                        passwordError = false
                    },
                    icon = {
                        Icon(
                            imageVector = Icons.Filled.Lock,
                            contentDescription = "Security Authorization",
                            tint = themeColor,
                            modifier = Modifier.size(28.dp)
                        )
                    },
                    title = {
                        Text(
                            text = "Authorization Required",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = TextPrimary
                        )
                    },
                    text = {
                        Column(
                            modifier = Modifier.fillMaxWidth(),
                            verticalArrangement = Arrangement.spacedBy(10.dp)
                        ) {
                            Text(
                                text = "Enter authorization password to start Maid Eclipse bot.",
                                fontSize = 13.sp,
                                color = TextSecondary
                            )

                            OutlinedTextField(
                                value = passwordInput,
                                onValueChange = {
                                    passwordInput = it
                                    if (passwordError) passwordError = false
                                },
                                label = { Text("Password") },
                                singleLine = true,
                                isError = passwordError,
                                supportingText = {
                                    if (passwordError) {
                                        Text(
                                            text = "Incorrect password! Please try again.",
                                            color = ErrorRed,
                                            fontSize = 11.sp
                                        )
                                    }
                                },
                                visualTransformation = if (passwordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                                trailingIcon = {
                                    IconButton(onClick = { passwordVisible = !passwordVisible }) {
                                        Icon(
                                            imageVector = if (passwordVisible) Icons.Filled.Visibility else Icons.Filled.VisibilityOff,
                                            contentDescription = if (passwordVisible) "Hide password" else "Show password",
                                            tint = TextMuted
                                        )
                                    }
                                },
                                modifier = Modifier.fillMaxWidth(),
                                colors = OutlinedTextFieldDefaults.colors(
                                    focusedBorderColor = themeColor,
                                    unfocusedBorderColor = Color(0xFF334155),
                                    errorBorderColor = ErrorRed,
                                    focusedTextColor = TextPrimary,
                                    unfocusedTextColor = TextPrimary
                                )
                            )
                        }
                    },
                    confirmButton = {
                        Button(
                            onClick = {
                                if (passwordInput.trim() == "tikus") {
                                    showPasswordDialog = false
                                    passwordInput = ""
                                    passwordError = false
                                    onStartParty()
                                } else {
                                    passwordError = true
                                }
                            },
                            colors = ButtonDefaults.buttonColors(containerColor = themeColor),
                            shape = RoundedCornerShape(8.dp)
                        ) {
                            Text(
                                text = "Start Bot",
                                fontWeight = FontWeight.Bold,
                                color = Color.White
                            )
                        }
                    },
                    dismissButton = {
                        TextButton(
                            onClick = {
                                showPasswordDialog = false
                                passwordInput = ""
                                passwordError = false
                            }
                        ) {
                            Text(
                                text = "Cancel",
                                color = TextSecondary
                            )
                        }
                    },
                    containerColor = Color(0xFF131522),
                    shape = RoundedCornerShape(16.dp)
                )
            }

            val activeMonsters =
                telemetryMap.values.firstOrNull { it.running && it.monsters.isNotEmpty() }?.monsters
                    ?: emptyList()
            val activeCell =
                telemetryMap.values.firstOrNull { it.running && it.cell.isNotEmpty() && it.cell != "-" }?.cell
                    ?: ""

            // Real-time Monster / Boss HP (Global for all party slots)
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

            // --- Slot Account ViewPager Tab Navigation ---
            ScrollableTabRow(
                selectedTabIndex = pagerState.currentPage,
                containerColor = Color(0xFF131522),
                contentColor = TextPrimary,
                edgePadding = 0.dp,
                indicator = { tabPositions ->
                    if (pagerState.currentPage < tabPositions.size) {
                        TabRowDefaults.SecondaryIndicator(
                            Modifier.tabIndicatorOffset(tabPositions[pagerState.currentPage]),
                            color = themeColor
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
                                        .background(if (slotTel.running) SuccessGreen else TextMuted)
                                )
                                Text(
                                    text = label,
                                    fontSize = 12.sp,
                                    fontWeight = if (selected) FontWeight.Bold else FontWeight.Medium,
                                    color = if (selected) themeColor else TextSecondary
                                )
                            }
                        }
                    )
                }
            }

            // --- ViewPager Content for Each Slot ---
            HorizontalPager(
                state = pagerState,
                modifier = Modifier.fillMaxWidth()
            ) { page ->
                val slotKey = slotKeys[page]
                val slotTitle = slotFullTitles[page]
                val slotConf = config.slots[slotKey] ?: SlotConfig()
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
                    modifier = Modifier
                        .fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    // 1. Slot Account Configuration & Live Telemetry
                    SlotCard(
                        slotKey = slotKey,
                        title = if (isRunning) slotConf.username.ifEmpty { slotTitle } else slotTitle,
                        config = slotConf,
                        telemetry = slotTel,
                        isPartyRunning = isRunning,
                        accentColor = themeColor,
                        showTauntToggle = false,
                        showEclipseTauntToggles = true,
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

@Preview(showBackground = true, backgroundColor = 0xFF0B0D14)
@Composable
private fun EclipseContentIdlePreview() {
    MyApplicationTheme {
        EclipseContent(
            config = EclipseConfig(
                server = "Alteon",
                roomNumber = 9099,
                slots = mapOf(
                    "slot1" to SlotConfig(
                        username = "LordLead",
                        charClass = "Lord of Order",
                        role = "master",
                        isTaunter = true
                    ),
                    "slot2" to SlotConfig(
                        username = "APTaunt",
                        charClass = "ArchPaladin",
                        role = "slave",
                        isTaunter = true
                    ),
                    "slot3" to SlotConfig(
                        username = "SCBuff",
                        charClass = "StoneCrusher",
                        role = "slave",
                        isTaunter = false
                    ),
                    "slot4" to SlotConfig(
                        username = "LRDps",
                        charClass = "Legion Revenant",
                        role = "slave",
                        isTaunter = false
                    )
                )
            ),
            telemetryMap = emptyMap(),
            logs = emptyList(),
            isRunning = false,
            onBack = {},
            onUpdateSettings = { _, _ -> },
            onUpdateSlot = { _, _ -> },
            onStartParty = {},
            onStopParty = {},
            onClearLogs = {}
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF0B0D14)
@Composable
private fun EclipseContentRunningPreview() {
    MyApplicationTheme {
        EclipseContent(
            config = EclipseConfig(
                server = "Alteon",
                roomNumber = 9099,
                slots = mapOf(
                    "slot1" to SlotConfig(
                        username = "LordLead",
                        charClass = "Lord of Order",
                        role = "master",
                        isTaunter = true
                    ),
                    "slot2" to SlotConfig(
                        username = "APTaunt",
                        charClass = "ArchPaladin",
                        role = "slave",
                        isTaunter = true
                    ),
                    "slot3" to SlotConfig(
                        username = "SCBuff",
                        charClass = "StoneCrusher",
                        role = "slave",
                        isTaunter = false
                    ),
                    "slot4" to SlotConfig(
                        username = "LRDps",
                        charClass = "Legion Revenant",
                        role = "slave",
                        isTaunter = false
                    )
                )
            ),
            telemetryMap = mapOf(
                "slot1" to SlotTelemetry(
                    running = true,
                    isConnected = true,
                    map = "ascendeclipse",
                    cell = "r3",
                    pad = "Left",
                    hp = 5000,
                    maxHp = 5000,
                    mp = 100,
                    maxMp = 100,
                    soeQty = 99,
                    monsters = listOf(
                        MonsterTelemetry(
                            monMapId = "1",
                            monName = "Ascended Midnight",
                            hp = 1250000,
                            maxHp = 2500000,
                            isAlive = true
                        ),
                        MonsterTelemetry(
                            monMapId = "2",
                            monName = "Ascended Solstice",
                            hp = 1850000,
                            maxHp = 2500000,
                            isAlive = true
                        )
                    )
                ),
                "slot2" to SlotTelemetry(
                    running = true,
                    isConnected = true,
                    map = "eclipse",
                    cell = "Boss",
                    pad = "Center",
                    hp = 4200,
                    maxHp = 4500,
                    mp = 85,
                    maxMp = 100,
                    soeQty = 80
                )
            ),
            partyStats = PartyStats(
                timeRunning = 4320L,
                clearedCount = 14
            ),
            logs = listOf(
                LogEntry(
                    botType = "eclipse",
                    username = "LordLead",
                    message = "Joined Eclipse dungeon"
                ),
                LogEntry(
                    botType = "eclipse",
                    username = "LordLead",
                    message = "Taunt cast on Eclipse Boss"
                ),
                LogEntry(
                    botType = "eclipse",
                    username = "APTaunt",
                    message = "Secondary taunt ready"
                )
            ),
            isRunning = true,
            onBack = {},
            onUpdateSettings = { _, _ -> },
            onUpdateSlot = { _, _ -> },
            onResetSettings = {},
            onStartParty = {},
            onStopParty = {},
            onClearLogs = {}
        )
    }
}
