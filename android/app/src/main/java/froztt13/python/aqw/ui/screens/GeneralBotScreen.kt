package froztt13.python.aqw.ui.screens

import android.Manifest
import android.os.Build
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.Extension
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.MilitaryTech
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material.icons.filled.Terminal
import androidx.compose.material.icons.filled.Tune
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MenuAnchorType
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.TabRowDefaults
import androidx.compose.material3.TabRowDefaults.tabIndicatorOffset
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
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
import froztt13.python.aqw.data.GeneralBotConfig
import froztt13.python.aqw.data.GeneralBotTelemetry
import froztt13.python.aqw.data.GeneralSubModuleInfo
import froztt13.python.aqw.data.GeneralTaskInfo
import froztt13.python.aqw.data.LogEntry
import froztt13.python.aqw.helper.BatteryOptimizationHelper
import froztt13.python.aqw.service.BotForegroundService
import froztt13.python.aqw.ui.components.ClassDropdown
import froztt13.python.aqw.ui.components.CustomOutlinedTextField
import froztt13.python.aqw.ui.components.DefaultTopBar
import froztt13.python.aqw.ui.components.LiveLogConsole
import froztt13.python.aqw.ui.components.ServerDropdown
import froztt13.python.aqw.ui.theme.BgDark
import froztt13.python.aqw.ui.theme.BorderDark
import froztt13.python.aqw.ui.theme.CardDark
import froztt13.python.aqw.ui.theme.ErrorRed
import froztt13.python.aqw.ui.theme.GeneralTeal
import froztt13.python.aqw.ui.theme.LegionBlue
import froztt13.python.aqw.ui.theme.MyApplicationTheme
import froztt13.python.aqw.ui.theme.PrimaryPurple
import froztt13.python.aqw.ui.theme.SuccessGreen
import froztt13.python.aqw.ui.theme.SunGold
import froztt13.python.aqw.ui.theme.SurfaceDark
import froztt13.python.aqw.ui.theme.TextMuted
import froztt13.python.aqw.ui.theme.TextPrimary
import froztt13.python.aqw.ui.theme.TextSecondary
import froztt13.python.aqw.viewmodel.GeneralBotViewModel

@Composable
fun GeneralBotScreen(
    onBack: () -> Unit,
    viewModel: GeneralBotViewModel = viewModel()
) {
    val context = LocalContext.current
    val config by viewModel.config.collectAsState()
    val telemetry by viewModel.telemetry.collectAsState()
    val isRunning by viewModel.isRunning.collectAsState()
    val subModules by viewModel.subModules.collectAsState()
    val logs by viewModel.logs.collectAsState()

    val notifPermissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { }

    LaunchedEffect(Unit) {
        viewModel.errorMessage.collect { msg ->
            Toast.makeText(context, msg, Toast.LENGTH_SHORT).show()
        }
    }

    GeneralBotContent(
        config = config,
        telemetry = telemetry,
        isRunning = isRunning,
        subModules = subModules,
        logs = logs,
        onBack = onBack,
        onResetState = {
            viewModel.resetState()
            BotForegroundService.stop(context)
        },
        onStart = {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
                !BatteryOptimizationHelper.hasNotificationPermission(context)
            ) {
                notifPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
            viewModel.startBot {
                BotForegroundService.start(
                    context,
                    "General Bot",
                    "Farm in progress..."
                )
            }
        },
        onStop = {
            viewModel.stopBot()
            BotForegroundService.stop(context)
        },
        onClearLogs = { viewModel.clearLogs() },
        onUpdateServer = { viewModel.updateServer(it) },
        onUpdateRoomNumber = { viewModel.updateRoomNumber(it) },
        onUpdateUsername = { viewModel.updateUsername(it) },
        onUpdatePassword = { viewModel.updatePassword(it) },
        onUpdateSubModule = { viewModel.updateSubModule(it) },
        onUpdateTask = { viewModel.updateTask(it) },
        onUpdateTargetQty = { viewModel.updateTargetQty(it) },
        onUpdateSoloClass = { viewModel.updateSoloClass(it) },
        onUpdateFarmClass = { viewModel.updateFarmClass(it) }
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun GeneralBotContent(
    config: GeneralBotConfig,
    telemetry: GeneralBotTelemetry,
    isRunning: Boolean,
    subModules: List<GeneralSubModuleInfo>,
    logs: List<LogEntry>,
    onBack: () -> Unit,
    onResetState: () -> Unit,
    onStart: () -> Unit,
    onStop: () -> Unit,
    onClearLogs: () -> Unit,
    onUpdateServer: (String) -> Unit,
    onUpdateRoomNumber: (Int) -> Unit,
    onUpdateUsername: (String) -> Unit,
    onUpdatePassword: (String) -> Unit,
    onUpdateSubModule: (String) -> Unit,
    onUpdateTask: (String) -> Unit,
    onUpdateTargetQty: (Int) -> Unit,
    onUpdateSoloClass: (String) -> Unit,
    onUpdateFarmClass: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    var selectedTab by remember { mutableIntStateOf(0) }
    var showResetConfirmDialog by remember { mutableStateOf(false) }

    if (showResetConfirmDialog) {
        AlertDialog(
            onDismissRequest = { showResetConfirmDialog = false },
            icon = {
                Icon(
                    imageVector = Icons.Filled.Warning,
                    contentDescription = "Reset State Confirmation",
                    tint = ErrorRed,
                    modifier = Modifier.size(28.dp)
                )
            },
            title = {
                Text(
                    text = "Reset Bot State?",
                    fontWeight = FontWeight.Bold,
                    color = TextPrimary
                )
            },
            text = {
                Text(
                    text = "This will forcefully stop the bot and reset its state back to Idle. Use this option if the bot is stuck or not responding to the stop command.",
                    color = TextSecondary,
                    fontSize = 13.sp
                )
            },
            confirmButton = {
                Button(
                    onClick = {
                        onResetState()
                        showResetConfirmDialog = false
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = ErrorRed)
                ) {
                    Text("Reset State", color = Color.White, fontWeight = FontWeight.Bold)
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

    Scaffold(
        modifier = modifier,
        containerColor = BgDark,
        topBar = {
            DefaultTopBar(
                title = "General Bot",
                onBack = onBack,
                containerColor = SurfaceDark,
                statusDotColor = GeneralTeal,
                actions = {
                    IconButton(
                        onClick = { showResetConfirmDialog = true }
                    ) {
                        Icon(
                            imageVector = Icons.Filled.Refresh,
                            contentDescription = "Reset State",
                            tint = TextSecondary
                        )
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Live Status Banner
            GeneralBotStatusHeader(
                telemetry = telemetry,
                isRunning = isRunning,
                onStart = onStart,
                onStop = onStop
            )

            // Tabs Row
            TabRow(
                selectedTabIndex = selectedTab,
                containerColor = SurfaceDark,
                contentColor = TextPrimary,
                indicator = { tabPositions ->
                    TabRowDefaults.SecondaryIndicator(
                        Modifier.tabIndicatorOffset(tabPositions[selectedTab]),
                        color = GeneralTeal
                    )
                }
            ) {
                Tab(
                    selected = selectedTab == 0,
                    onClick = { selectedTab = 0 },
                    text = {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(6.dp)
                        ) {
                            Icon(
                                Icons.Filled.Tune,
                                contentDescription = null,
                                modifier = Modifier.size(16.dp)
                            )
                            Text("Setup", fontWeight = FontWeight.Medium)
                        }
                    },
                    selectedContentColor = GeneralTeal,
                    unselectedContentColor = TextSecondary
                )
                Tab(
                    selected = selectedTab == 1,
                    onClick = { selectedTab = 1 },
                    text = {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(6.dp)
                        ) {
                            Icon(
                                Icons.Filled.MilitaryTech,
                                contentDescription = null,
                                modifier = Modifier.size(16.dp)
                            )
                            Text("Telemetry", fontWeight = FontWeight.Medium)
                        }
                    },
                    selectedContentColor = GeneralTeal,
                    unselectedContentColor = TextSecondary
                )
                Tab(
                    selected = selectedTab == 2,
                    onClick = { selectedTab = 2 },
                    text = {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(6.dp)
                        ) {
                            Icon(
                                Icons.Filled.Terminal,
                                contentDescription = null,
                                modifier = Modifier.size(16.dp)
                            )
                            Text("Console", fontWeight = FontWeight.Medium)
                        }
                    },
                    selectedContentColor = GeneralTeal,
                    unselectedContentColor = TextSecondary
                )
            }

            // Tab Content
            when (selectedTab) {
                0 -> {
                    SetupTabContent(
                        config = config,
                        isRunning = isRunning,
                        subModules = subModules,
                        onUpdateServer = onUpdateServer,
                        onUpdateRoomNumber = onUpdateRoomNumber,
                        onUpdateUsername = onUpdateUsername,
                        onUpdatePassword = onUpdatePassword,
                        onUpdateSubModule = onUpdateSubModule,
                        onUpdateTask = onUpdateTask,
                        onUpdateTargetQty = onUpdateTargetQty,
                        onUpdateSoloClass = onUpdateSoloClass,
                        onUpdateFarmClass = onUpdateFarmClass,
                        onStart = onStart,
                        onStop = onStop
                    )
                }

                1 -> {
                    TelemetryTabContent(telemetry = telemetry)
                }

                2 -> {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(12.dp)
                    ) {
                        LiveLogConsole(
                            logs = logs,
                            onClearLogs = onClearLogs,
                            modifier = Modifier.fillMaxSize()
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun GeneralBotStatusHeader(
    telemetry: GeneralBotTelemetry,
    isRunning: Boolean,
    onStart: () -> Unit,
    onStop: () -> Unit
) {
    val statusColor = when (telemetry.status.lowercase()) {
        "running" -> SuccessGreen
        "starting", "connecting" -> LegionBlue
        "error" -> ErrorRed
        "finished" -> SuccessGreen
        else -> TextMuted
    }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(12.dp),
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(containerColor = CardDark),
        border = BorderStroke(1.dp, BorderDark)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Box(
                            modifier = Modifier
                                .size(10.dp)
                                .clip(CircleShape)
                                .background(statusColor)
                        )
                        Text(
                            text = if (isRunning) telemetry.status else "Idle",
                            color = statusColor,
                            fontWeight = FontWeight.Bold,
                            fontSize = 15.sp
                        )
                    }

                    Text(
                        text = if (isRunning) {
                            val mapInfo =
                                if (telemetry.map != "-") "${telemetry.map} (${telemetry.cell})" else "In transit..."
                            "$mapInfo • ${telemetry.formattedTime}"
                        } else {
                            "Ready to farm"
                        },
                        color = TextSecondary,
                        fontSize = 12.sp
                    )
                }

                Button(
                    onClick = { if (isRunning) onStop() else onStart() },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (isRunning) ErrorRed else GeneralTeal
                    ),
                    shape = RoundedCornerShape(10.dp),
                    contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp)
                ) {
                    Icon(
                        imageVector = if (isRunning) Icons.Filled.Stop else Icons.Filled.PlayArrow,
                        contentDescription = null,
                        modifier = Modifier.size(18.dp)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = if (isRunning) "Stop" else "Start",
                        fontWeight = FontWeight.SemiBold,
                        fontSize = 13.sp
                    )
                }
            }
        }
    }
}

@Composable
fun SkillCooldownsRow(
    cooldowns: Map<Int, Double>,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        for (i in 0..5) {
            val cd = cooldowns[i] ?: 0.0
            val isReady = cd <= 0.0
            val isItem = i == 5
            val label = if (isItem) "Item" else "$i"

            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(2.dp)
            ) {
                Box(
                    modifier = Modifier
                        .size(34.dp)
                        .clip(RoundedCornerShape(6.dp))
                        .background(
                            when {
                                !isReady -> Color(0xFF1E2130)
                                isItem -> SunGold.copy(alpha = 0.25f)
                                else -> GeneralTeal.copy(alpha = 0.2f)
                            }
                        )
                        .border(
                            1.dp,
                            when {
                                !isReady -> Color(0xFF2E3350)
                                isItem -> SunGold.copy(alpha = 0.6f)
                                else -> GeneralTeal.copy(alpha = 0.5f)
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
                            isItem -> SunGold
                            else -> TextPrimary
                        }
                    )
                }
                Text(
                    text = if (isItem) "Pot" else if (i == 0) "Auto" else "S$i",
                    fontSize = 8.sp,
                    color = TextMuted
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SetupTabContent(
    config: GeneralBotConfig,
    isRunning: Boolean,
    subModules: List<GeneralSubModuleInfo>,
    onUpdateServer: (String) -> Unit,
    onUpdateRoomNumber: (Int) -> Unit,
    onUpdateUsername: (String) -> Unit,
    onUpdatePassword: (String) -> Unit,
    onUpdateSubModule: (String) -> Unit,
    onUpdateTask: (String) -> Unit,
    onUpdateTargetQty: (Int) -> Unit,
    onUpdateSoloClass: (String) -> Unit,
    onUpdateFarmClass: (String) -> Unit,
    onStart: () -> Unit,
    onStop: () -> Unit
) {
    var passwordVisible by remember { mutableStateOf(false) }
    val currentSubModule = subModules.find { it.id == config.subModule } ?: subModules.firstOrNull()
    val availableTasks = currentSubModule?.tasks ?: emptyList()
    val currentTask = availableTasks.find { it.id == config.task } ?: availableTasks.firstOrNull()

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(12.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        // Sub-Module Selection Card
        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = CardDark),
                border = BorderStroke(1.dp, LegionBlue.copy(alpha = 0.3f))
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
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Filled.Extension,
                                contentDescription = null,
                                tint = LegionBlue,
                                modifier = Modifier.size(20.dp)
                            )
                            Text(
                                text = "Bot Sub-Module",
                                color = TextPrimary,
                                fontWeight = FontWeight.Bold,
                                fontSize = 15.sp
                            )
                        }

                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(6.dp))
                                .background(LegionBlue.copy(alpha = 0.15f))
                                .padding(horizontal = 8.dp, vertical = 2.dp)
                        ) {
                            Text(
                                text = currentSubModule?.category ?: "Class Farm",
                                color = LegionBlue,
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Medium
                            )
                        }
                    }

                    // Dropdown for Submodules
                    var subModuleExpanded by remember { mutableStateOf(false) }
                    ExposedDropdownMenuBox(
                        expanded = subModuleExpanded && !isRunning,
                        onExpandedChange = {
                            if (!isRunning) subModuleExpanded = !subModuleExpanded
                        }
                    ) {
                        CustomOutlinedTextField(
                            value = currentSubModule?.name ?: "Legion Revenant Farm",
                            onValueChange = {},
                            readOnly = true,
                            enabled = !isRunning,
                            label = { Text("Selected Sub-Module") },
                            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = subModuleExpanded) },
                            modifier = Modifier
                                .fillMaxWidth()
                                .menuAnchor(
                                    MenuAnchorType.PrimaryNotEditable,
                                    enabled = !isRunning
                                )
                        )

                        ExposedDropdownMenu(
                            expanded = subModuleExpanded && !isRunning,
                            onDismissRequest = { subModuleExpanded = false },
                            modifier = Modifier.background(CardDark)
                        ) {
                            if (subModules.isEmpty()) {
                                DropdownMenuItem(
                                    text = { Text("Legion Revenant Farm", color = TextPrimary) },
                                    onClick = {
                                        onUpdateSubModule("lr")
                                        subModuleExpanded = false
                                    }
                                )
                            } else {
                                subModules.forEach { sub ->
                                    DropdownMenuItem(
                                        text = {
                                            Column {
                                                Text(
                                                    sub.name,
                                                    color = TextPrimary,
                                                    fontWeight = FontWeight.SemiBold
                                                )
                                                Text(
                                                    sub.description,
                                                    color = TextSecondary,
                                                    fontSize = 11.sp
                                                )
                                            }
                                        },
                                        onClick = {
                                            onUpdateSubModule(sub.id)
                                            subModuleExpanded = false
                                        }
                                    )
                                }
                            }
                        }
                    }

                    Text(
                        text = currentSubModule?.description
                            ?: "Automated Legion Revenant farming: Fealty 1, Fealty 2, Fealty 3, and Legion Tokens.",
                        color = TextSecondary,
                        fontSize = 12.sp
                    )
                }
            }
        }

        // Task & Target Quantity Card
        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = CardDark),
                border = BorderStroke(1.dp, BorderDark)
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Filled.MilitaryTech,
                            contentDescription = null,
                            tint = GeneralTeal,
                            modifier = Modifier.size(20.dp)
                        )
                        Text(
                            text = "Farming Task & Goal",
                            color = TextPrimary,
                            fontWeight = FontWeight.Bold,
                            fontSize = 15.sp
                        )
                    }

                    // Task Dropdown
                    var taskExpanded by remember { mutableStateOf(false) }
                    ExposedDropdownMenuBox(
                        expanded = taskExpanded && !isRunning,
                        onExpandedChange = { if (!isRunning) taskExpanded = !taskExpanded }
                    ) {
                        CustomOutlinedTextField(
                            value = currentTask?.name ?: "Revenant's Spellscroll",
                            onValueChange = {},
                            readOnly = true,
                            enabled = !isRunning,
                            label = { Text("Task / Quest") },
                            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = taskExpanded) },
                            modifier = Modifier
                                .fillMaxWidth()
                                .menuAnchor(
                                    MenuAnchorType.PrimaryNotEditable,
                                    enabled = !isRunning
                                )
                        )

                        ExposedDropdownMenu(
                            expanded = taskExpanded && !isRunning,
                            onDismissRequest = { taskExpanded = false },
                            modifier = Modifier.background(CardDark)
                        ) {
                            availableTasks.forEach { t ->
                                DropdownMenuItem(
                                    text = {
                                        Column {
                                            Row(
                                                horizontalArrangement = Arrangement.spacedBy(8.dp),
                                                verticalAlignment = Alignment.CenterVertically
                                            ) {
                                                Text(
                                                    t.name,
                                                    color = TextPrimary,
                                                    fontWeight = FontWeight.Medium
                                                )
                                                if (t.questId > 0) {
                                                    Text(
                                                        text = "Q#${t.questId}",
                                                        color = GeneralTeal,
                                                        fontSize = 11.sp,
                                                        fontWeight = FontWeight.Bold
                                                    )
                                                }
                                            }
                                            Text(
                                                t.description,
                                                color = TextSecondary,
                                                fontSize = 11.sp
                                            )
                                        }
                                    },
                                    onClick = {
                                        onUpdateTask(t.id)
                                        taskExpanded = false
                                    }
                                )
                            }
                        }
                    }

                    // Task details note
                    // Task details note
                    if (currentTask != null) {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clip(RoundedCornerShape(8.dp))
                                .background(SurfaceDark)
                                .padding(10.dp)
                        ) {
                            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                Text(
                                    text = currentTask.description,
                                    color = TextSecondary,
                                    fontSize = 12.sp
                                )
                                if (currentTask.trackedItem.isNotBlank()) {
                                    Text(
                                        text = "Tracked Item: ${currentTask.trackedItem}",
                                        color = GeneralTeal,
                                        fontSize = 11.sp,
                                        fontWeight = FontWeight.SemiBold
                                    )
                                } else {
                                    Text(
                                        text = "Mode: Infinite Loop (Continuous farm, no item limit)",
                                        color = GeneralTeal,
                                        fontSize = 11.sp,
                                        fontWeight = FontWeight.SemiBold
                                    )
                                }
                            }
                        }
                    }

                    // Target Quantity or Infinite Loop Banner
                    if (currentTask != null && currentTask.trackedItem.isBlank()) {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clip(RoundedCornerShape(10.dp))
                                .background(SurfaceDark)
                                .border(1.dp, BorderDark, RoundedCornerShape(10.dp))
                                .padding(12.dp)
                        ) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                                    Text(
                                        text = "Continuous Farm (Infinite)",
                                        color = TextPrimary,
                                        fontWeight = FontWeight.SemiBold,
                                        fontSize = 13.sp
                                    )
                                    Text(
                                        text = "Runs endlessly until stopped. Reward drops are gathered automatically.",
                                        color = TextSecondary,
                                        fontSize = 11.sp
                                    )
                                }
                                Box(
                                    modifier = Modifier
                                        .clip(RoundedCornerShape(6.dp))
                                        .background(GeneralTeal.copy(alpha = 0.15f))
                                        .padding(horizontal = 8.dp, vertical = 2.dp)
                                ) {
                                    Text(
                                        text = "∞ Loop",
                                        color = GeneralTeal,
                                        fontSize = 12.sp,
                                        fontWeight = FontWeight.Bold
                                    )
                                }
                            }
                        }
                    } else {
                        // Target Quantity
                        Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                            Text(
                                text = "Target Quantity",
                                color = TextSecondary,
                                fontSize = 13.sp,
                                fontWeight = FontWeight.Medium
                            )

                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(8.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                CustomOutlinedTextField(
                                    value = config.targetQty.toString(),
                                    onValueChange = { str ->
                                        val num = str.filter { it.isDigit() }.toIntOrNull()
                                        if (num != null) onUpdateTargetQty(num)
                                    },
                                    enabled = !isRunning,
                                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                                    modifier = Modifier.weight(1f),
                                    contentPadding = PaddingValues(
                                        horizontal = 12.dp,
                                        vertical = 10.dp
                                    )
                                )

                                // Quick preset buttons based on task
                                val presets = when (config.task) {
                                    "spellscroll" -> listOf(1, 5, 20)
                                    "conquest_wreath" -> listOf(1, 3, 6)
                                    "exalted_crown" -> listOf(1, 5, 10)
                                    "legion_token" -> listOf(1000, 4000, 25000)
                                    "larvae_uni13" -> listOf(1, 3, 13)
                                    "larvae_diamond" -> listOf(50, 100, 1000)
                                    "larvae_dcs" -> listOf(10, 50, 100)
                                    "larvae_tainted" -> listOf(20, 100, 500)
                                    "larvae_voucher_nonmem" -> listOf(1, 2)
                                    "larvae_totem" -> listOf(5, 10, 30)
                                    "larvae_gem" -> listOf(20, 50, 100)
                                    "larvae_blood_gem" -> listOf(5, 10, 30)
                                    else -> listOf(10, 50, 100)
                                }

                                presets.forEach { preset ->
                                    OutlinedButton(
                                        onClick = { onUpdateTargetQty(preset) },
                                        enabled = !isRunning,
                                        contentPadding = PaddingValues(
                                            horizontal = 10.dp,
                                            vertical = 6.dp
                                        ),
                                        shape = RoundedCornerShape(8.dp),
                                        border = BorderStroke(
                                            1.dp,
                                            if (config.targetQty == preset) GeneralTeal else BorderDark
                                        )
                                    ) {
                                        Text(
                                            text = "$preset",
                                            fontSize = 12.sp,
                                            color = if (config.targetQty == preset) GeneralTeal else TextSecondary
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // Account Credentials Card
        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = CardDark),
                border = BorderStroke(1.dp, BorderDark)
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Filled.Person,
                            contentDescription = null,
                            tint = PrimaryPurple,
                            modifier = Modifier.size(20.dp)
                        )
                        Text(
                            text = "Account Credentials",
                            color = TextPrimary,
                            fontWeight = FontWeight.Bold,
                            fontSize = 15.sp
                        )
                    }

                    // Server & Room Number Row
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(10.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        ServerDropdown(
                            selectedServer = config.server,
                            enabled = !isRunning,
                            onServerSelected = onUpdateServer,
                            modifier = Modifier.weight(1f)
                        )

                        CustomOutlinedTextField(
                            value = if (config.roomNumber == 0) "" else config.roomNumber.toString(),
                            onValueChange = { str ->
                                val num = str.filter { it.isDigit() }.toIntOrNull() ?: 0
                                onUpdateRoomNumber(num)
                            },
                            enabled = !isRunning,
                            label = { Text("Room #") },
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                            modifier = Modifier.weight(1f),
                        )
                    }

                    // Username
                    CustomOutlinedTextField(
                        value = config.username,
                        onValueChange = onUpdateUsername,
                        enabled = !isRunning,
                        label = { Text("Username") },
                        leadingIcon = {
                            Icon(
                                Icons.Filled.Person,
                                contentDescription = null,
                                tint = TextSecondary,
                                modifier = Modifier.size(18.dp)
                            )
                        },
                        modifier = Modifier.fillMaxWidth()
                    )

                    // Password
                    CustomOutlinedTextField(
                        value = config.password,
                        onValueChange = onUpdatePassword,
                        enabled = !isRunning,
                        label = { Text("Password") },
                        leadingIcon = {
                            Icon(
                                Icons.Filled.Lock,
                                contentDescription = null,
                                tint = TextSecondary,
                                modifier = Modifier.size(18.dp)
                            )
                        },
                        trailingIcon = {
                            IconButton(onClick = { passwordVisible = !passwordVisible }) {
                                Icon(
                                    imageVector = if (passwordVisible) Icons.Filled.Visibility else Icons.Filled.VisibilityOff,
                                    contentDescription = null,
                                    tint = TextSecondary,
                                    modifier = Modifier.size(18.dp)
                                )
                            }
                        },
                        visualTransformation = if (passwordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }
        }

        // Combat Class Setup Card
        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = CardDark),
                border = BorderStroke(1.dp, BorderDark)
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Filled.Shield,
                            contentDescription = null,
                            tint = LegionBlue,
                            modifier = Modifier.size(20.dp)
                        )
                        Text(
                            text = "Dynamic Class Setup",
                            color = TextPrimary,
                            fontWeight = FontWeight.Bold,
                            fontSize = 15.sp
                        )
                    }

                    Text(
                        text = "The bot automatically swaps between Solo Class and Farm Class depending on whether it is fighting a single boss (e.g. Ultra Aeacus) or mob enemies.",
                        color = TextSecondary,
                        fontSize = 12.sp
                    )

                    // Solo Class
                    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text("Solo Class (Boss Killer)", color = TextSecondary, fontSize = 12.sp)
                        ClassDropdown(
                            selectedClass = config.soloClass,
                            enabled = !isRunning,
                            onClassSelected = onUpdateSoloClass,
                            modifier = Modifier.fillMaxWidth()
                        )
                    }

                    // Farm Class
                    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text(
                            "Farm Class (Multi-target / Mob)",
                            color = TextSecondary,
                            fontSize = 12.sp
                        )
                        ClassDropdown(
                            selectedClass = config.farmClass,
                            enabled = !isRunning,
                            onClassSelected = onUpdateFarmClass,
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                }
            }
        }

        item {
            Spacer(modifier = Modifier.height(24.dp))
        }
    }
}

@Composable
fun TelemetryTabContent(telemetry: GeneralBotTelemetry) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(12.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        // Hero Progress Card
        if (telemetry.running)
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(14.dp),
                    colors = CardDefaults.cardColors(containerColor = CardDark),
                    border = BorderStroke(1.dp, GeneralTeal.copy(alpha = 0.4f))
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        if (telemetry.trackedItem.isBlank()) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Column {
                                    Text(
                                        text = "Farming Mode",
                                        color = TextSecondary,
                                        fontSize = 12.sp
                                    )
                                    Text(
                                        text = "Infinite Turn-in Loop",
                                        color = TextPrimary,
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 18.sp
                                    )
                                }

                                Box(
                                    modifier = Modifier
                                        .clip(RoundedCornerShape(8.dp))
                                        .background(GeneralTeal.copy(alpha = 0.2f))
                                        .padding(horizontal = 10.dp, vertical = 4.dp)
                                ) {
                                    Text(
                                        text = "∞ Loop",
                                        color = GeneralTeal,
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 14.sp
                                    )
                                }
                            }

                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text(
                                    text = "Turn-ins Completed: ${telemetry.currentQty}",
                                    color = TextPrimary,
                                    fontWeight = FontWeight.SemiBold,
                                    fontSize = 13.sp
                                )
                                Text(
                                    text = "Goal: Continuous",
                                    color = TextSecondary,
                                    fontSize = 13.sp
                                )
                            }
                        } else {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Column {
                                    Text(
                                        text = "Item Goal Progress",
                                        color = TextSecondary,
                                        fontSize = 12.sp
                                    )
                                    Text(
                                        text = telemetry.trackedItem,
                                        color = TextPrimary,
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 18.sp
                                    )
                                }

                                Box(
                                    modifier = Modifier
                                        .clip(RoundedCornerShape(8.dp))
                                        .background(GeneralTeal.copy(alpha = 0.2f))
                                        .padding(horizontal = 10.dp, vertical = 4.dp)
                                ) {
                                    Text(
                                        text = "${telemetry.progressPercent}%",
                                        color = GeneralTeal,
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 15.sp
                                    )
                                }
                            }

                            // Progress Bar
                            LinearProgressIndicator(
                                progress = { telemetry.progressFraction },
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(10.dp)
                                    .clip(RoundedCornerShape(5.dp)),
                                color = GeneralTeal,
                                trackColor = BorderDark
                            )

                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text(
                                    text = "Collected: ${telemetry.currentQty}",
                                    color = TextPrimary,
                                    fontWeight = FontWeight.SemiBold,
                                    fontSize = 13.sp
                                )
                                Text(
                                    text = "Target: ${telemetry.targetQty}",
                                    color = TextSecondary,
                                    fontSize = 13.sp
                                )
                            }
                        }
                    }
                }
            }

        // Live Action Status Card
        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = CardDark),
                border = BorderStroke(1.dp, BorderDark)
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Filled.AutoAwesome,
                            contentDescription = null,
                            tint = LegionBlue,
                            modifier = Modifier.size(18.dp)
                        )
                        Text(
                            text = "Current Activity",
                            color = TextPrimary,
                            fontWeight = FontWeight.Bold,
                            fontSize = 14.sp
                        )
                    }

                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(8.dp))
                            .background(SurfaceDark)
                            .padding(12.dp)
                    ) {
                        Text(
                            text = telemetry.message.ifEmpty { "Waiting for bot activity..." },
                            color = TextPrimary,
                            fontSize = 13.sp
                        )
                    }
                }
            }
        }

        // Player Vitals Card
        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = CardDark),
                border = BorderStroke(1.dp, BorderDark)
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Filled.Favorite,
                            contentDescription = null,
                            tint = ErrorRed,
                            modifier = Modifier.size(18.dp)
                        )
                        Text(
                            text = "Player Status",
                            color = TextPrimary,
                            fontWeight = FontWeight.Bold,
                            fontSize = 14.sp
                        )
                    }

                    // HP Bar
                    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text("Health (HP)", color = TextSecondary, fontSize = 12.sp)
                            Text(
                                "${telemetry.hp} / ${telemetry.maxHp}",
                                color = TextPrimary,
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Medium
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
                            trackColor = BorderDark
                        )
                    }

                    // MP Bar
                    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text("Mana (MP)", color = TextSecondary, fontSize = 12.sp)
                            Text(
                                "${telemetry.mp} / ${telemetry.maxMp}",
                                color = TextPrimary,
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Medium
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
                            color = LegionBlue,
                            trackColor = BorderDark
                        )
                    }

                    // Skill Cooldowns
                    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text("Skill Cooldowns", color = TextSecondary, fontSize = 12.sp)
                        SkillCooldownsRow(cooldowns = telemetry.cooldowns)
                    }

                    // Location Details
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(4.dp)
                        ) {
                            Icon(
                                Icons.Filled.LocationOn,
                                contentDescription = null,
                                tint = TextSecondary,
                                modifier = Modifier.size(14.dp)
                            )
                            Text("Map: ${telemetry.map}", color = TextSecondary, fontSize = 12.sp)
                        }
                        Text(
                            "Cell: ${telemetry.cell} (${telemetry.pad})",
                            color = TextSecondary,
                            fontSize = 12.sp
                        )
                    }
                }
            }
        }
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF0B0D14)
@Composable
private fun GeneralBotContentIdlePreview() {
    MyApplicationTheme {
        GeneralBotContent(
            config = GeneralBotConfig(
                server = "Alteon",
                roomNumber = 9099,
                username = "HeroAQW",
                soloClass = "Void Highlord",
                farmClass = "Legion Revenant"
            ),
            telemetry = GeneralBotTelemetry(
                status = "Idle",
                message = "Ready to start"
            ),
            isRunning = false,
            subModules = listOf(
                GeneralSubModuleInfo(
                    id = "lr",
                    name = "Legion Revenant Farm",
                    category = "Class Farm",
                    description = "Automated farming for Legion Revenant classes and prerequisites",
                    tasks = listOf(
                        GeneralTaskInfo(
                            "spellscroll",
                            "Revenant's Spellscroll",
                            "Farm Spellscrolls",
                            20,
                            "Revenant's Spellscroll"
                        ),
                        GeneralTaskInfo(
                            "conquest_wreath",
                            "Conquest Wreath",
                            "Farm Conquest Wreaths",
                            6,
                            "Conquest Wreath"
                        )
                    )
                ),
                GeneralSubModuleInfo(
                    id = "nulgath",
                    name = "Nulgath Materials",
                    category = "Nulgath Farm",
                    description = "Nulgath reagents and quest turn-ins",
                    tasks = listOf(
                        GeneralTaskInfo(
                            "larvae_turnins",
                            "Nulgath Larva (Turn-ins)",
                            "Turn in Nulgath Larva quest continuously",
                            1,
                            ""
                        )
                    )
                )
            ),
            logs = listOf(
                LogEntry(
                    botType = "general",
                    username = "HeroAQW",
                    message = "[General Bot] Initialized successfully"
                )
            ),
            onBack = {},
            onResetState = {},
            onStart = {},
            onStop = {},
            onClearLogs = {},
            onUpdateServer = {},
            onUpdateRoomNumber = {},
            onUpdateUsername = {},
            onUpdatePassword = {},
            onUpdateSubModule = {},
            onUpdateTask = {},
            onUpdateTargetQty = {},
            onUpdateSoloClass = {},
            onUpdateFarmClass = {}
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF0B0D14)
@Composable
private fun GeneralBotContentRunningPreview() {
    MyApplicationTheme {
        GeneralBotContent(
            config = GeneralBotConfig(
                server = "Alteon",
                roomNumber = 9099,
                username = "HeroAQW",
                soloClass = "Void Highlord",
                farmClass = "Legion Revenant"
            ),
            telemetry = GeneralBotTelemetry(
                running = true,
                isConnected = true,
                status = "Running",
                message = "Attacking Mana Golem in /elemental...",
                subModule = "nulgath",
                subModuleName = "Nulgath Materials",
                task = "larvae_turnins",
                taskName = "Nulgath Larva (Turn-ins)",
                currentQty = 14,
                targetQty = 0,
                map = "elemental",
                cell = "r3",
                pad = "Spawn",
                hp = 3500,
                maxHp = 3500,
                mp = 200,
                maxMp = 200,
                cooldowns = mapOf(0 to 0.0, 1 to 2.1, 2 to 0.0, 3 to 4.5, 4 to 0.0, 5 to 0.0),
                timeRunning = 620
            ),
            isRunning = true,
            subModules = listOf(
                GeneralSubModuleInfo(
                    id = "nulgath",
                    name = "Nulgath Materials",
                    category = "Nulgath Farm",
                    description = "Nulgath reagents and quest turn-ins",
                    tasks = listOf(
                        GeneralTaskInfo(
                            "larvae_turnins",
                            "Nulgath Larva (Turn-ins)",
                            "Turn in Nulgath Larva quest continuously",
                            1,
                            ""
                        )
                    )
                )
            ),
            logs = listOf(
                LogEntry(
                    botType = "general",
                    username = "HeroAQW",
                    message = "[General Bot] Connected to Alteon"
                ),
                LogEntry(
                    botType = "general",
                    username = "HeroAQW",
                    message = "[General Bot] Joined elemental-9099"
                ),
                LogEntry(
                    botType = "general",
                    username = "HeroAQW",
                    message = "[General Bot] Mana Golem defeated, turning in quest..."
                )
            ),
            onBack = {},
            onResetState = {},
            onStart = {},
            onStop = {},
            onClearLogs = {},
            onUpdateServer = {},
            onUpdateRoomNumber = {},
            onUpdateUsername = {},
            onUpdatePassword = {},
            onUpdateSubModule = {},
            onUpdateTask = {},
            onUpdateTargetQty = {},
            onUpdateSoloClass = {},
            onUpdateFarmClass = {}
        )
    }
}
