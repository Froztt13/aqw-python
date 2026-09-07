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
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.List
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.DragHandle
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.People
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Star
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
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.TabRowDefaults
import androidx.compose.material3.TabRowDefaults.tabIndicatorOffset
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
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
import froztt13.python.aqw.data.DoomAccount
import froztt13.python.aqw.data.DoomAccountTelemetry
import froztt13.python.aqw.data.LogEntry
import froztt13.python.aqw.data.WeeklyDoomConfig
import froztt13.python.aqw.data.WeeklyDoomTelemetry
import froztt13.python.aqw.helper.BatteryOptimizationHelper
import froztt13.python.aqw.service.BotForegroundService
import froztt13.python.aqw.ui.components.LiveLogConsole
import froztt13.python.aqw.ui.components.ServerDropdown
import froztt13.python.aqw.ui.theme.BgDark
import froztt13.python.aqw.ui.theme.BorderDark
import froztt13.python.aqw.ui.theme.CardDark
import froztt13.python.aqw.ui.theme.DoomCrimson
import froztt13.python.aqw.ui.theme.DoomGold
import froztt13.python.aqw.ui.theme.ErrorRed
import froztt13.python.aqw.ui.theme.MoonCyan
import froztt13.python.aqw.ui.theme.MyApplicationTheme
import froztt13.python.aqw.ui.theme.PrimaryPurple
import froztt13.python.aqw.ui.theme.SuccessGreen
import froztt13.python.aqw.ui.theme.SunGold
import froztt13.python.aqw.ui.theme.SurfaceDark
import froztt13.python.aqw.ui.theme.TextMuted
import froztt13.python.aqw.ui.theme.TextPrimary
import froztt13.python.aqw.ui.theme.TextSecondary
import froztt13.python.aqw.viewmodel.WeeklyDoomViewModel
import sh.calvin.reorderable.ReorderableItem
import sh.calvin.reorderable.rememberReorderableLazyListState

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WeeklyDoomBotScreen(
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: WeeklyDoomViewModel = viewModel()
) {
    WeeklyDoomScreen(onBack = onBack, modifier = modifier, viewModel = viewModel)
}

@Composable
fun WeeklyDoomScreen(
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: WeeklyDoomViewModel = viewModel()
) {
    val context = LocalContext.current
    val config by viewModel.doomConfig.collectAsState()
    val telemetry by viewModel.doomStatus.collectAsState()
    val isRunning by viewModel.isRunning.collectAsState()
    val logs by viewModel.doomLogs.collectAsState()

    val notifPermissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { /* Ignored */ }

    // Collect one-time error messages
    LaunchedEffect(Unit) {
        viewModel.errorMessage.collect { err ->
            Toast.makeText(context, err, Toast.LENGTH_LONG).show()
        }
    }

    WeeklyDoomContent(
        config = config,
        telemetry = telemetry,
        logs = logs,
        isRunning = isRunning,
        onBack = onBack,
        onStart = {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
                !BatteryOptimizationHelper.hasNotificationPermission(context)
            ) {
                notifPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
            viewModel.startDoom { success, _ ->
                if (success) {
                    BotForegroundService.start(
                        context,
                        "Weekly Doom Bot",
                        "Processing accounts in background..."
                    )
                }
            }
        },
        onStop = {
            viewModel.stopDoom()
            BotForegroundService.stop(context)
        },
        onUpdateServer = { viewModel.updateServer(it) },
        onAddAccount = { username, password ->
            viewModel.addAccount(username, password)
        },
        onUpdateAccount = { id, username, password ->
            viewModel.updateAccount(id, username, password)
        },
        onToggleAccount = { id, enabled ->
            viewModel.toggleAccount(id, enabled)
        },
        onRemoveAccount = { id ->
            viewModel.removeAccount(id)
        },
        onMoveAccount = { fromIndex, toIndex ->
            viewModel.moveAccount(fromIndex, toIndex)
        },
        onClearLogs = { viewModel.clearLogs() },
        modifier = modifier
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WeeklyDoomContent(
    config: WeeklyDoomConfig,
    telemetry: WeeklyDoomTelemetry,
    logs: List<LogEntry>,
    isRunning: Boolean,
    onBack: () -> Unit,
    onStart: () -> Unit,
    onStop: () -> Unit,
    onUpdateServer: (String) -> Unit,
    onAddAccount: (username: String, password: String) -> Unit,
    onUpdateAccount: (id: String, username: String, password: String) -> Unit,
    onToggleAccount: (id: String, enabled: Boolean) -> Unit,
    onRemoveAccount: (id: String) -> Unit,
    onMoveAccount: (fromIndex: Int, toIndex: Int) -> Unit,
    onClearLogs: () -> Unit,
    modifier: Modifier = Modifier,
    initialTabIndex: Int = 0,
    initialShowSettings: Boolean = false
) {
    var showSettings by remember { mutableStateOf(initialShowSettings) }
    var selectedTabIndex by remember { mutableIntStateOf(initialTabIndex) }

    // Account Add / Edit Dialog State
    var showAccountDialog by remember { mutableStateOf(false) }
    var editingAccount by remember { mutableStateOf<DoomAccount?>(null) }
    var dialogUsername by remember { mutableStateOf("") }
    var dialogPassword by remember { mutableStateOf("") }
    var dialogPasswordVisible by remember { mutableStateOf(false) }

    // Delete Confirmation Dialog State
    var accountToDelete by remember { mutableStateOf<DoomAccount?>(null) }

    Scaffold(
        modifier = modifier.fillMaxSize(),
        containerColor = BgDark,
        topBar = {
            TopAppBar(
                title = {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        Box(

                            modifier = Modifier
                                .size(10.dp)
                                .clip(CircleShape)
                                .background(if (isRunning) SuccessGreen else DoomCrimson)
                        )
                        Text(
                            text = "WEEKLY DOOM BOT",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = TextPrimary
                        )
                    }
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
                    IconButton(
                        onClick = { showSettings = !showSettings },
                        modifier = Modifier
                            .clip(CircleShape)
                            .background(if (showSettings) DoomCrimson.copy(alpha = 0.2f) else Color.Transparent)
                    ) {
                        Icon(
                            imageVector = Icons.Filled.Settings,
                            contentDescription = "Toggle Settings",
                            tint = if (showSettings) DoomCrimson else TextSecondary
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
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // 1. Session Overview & Status Banner
            WeeklyDoomStatsBar(
                isRunning = isRunning,
                telemetry = telemetry
            )

            // 2. Start / Stop Action Controls
            WeeklyDoomActionControls(
                isRunning = isRunning,
                onStart = onStart,
                onStop = onStop
            )

            // 3. Global Server Configuration (Hideable with TopAppBar Settings button)
            AnimatedVisibility(
                visible = showSettings,
                enter = fadeIn() + expandVertically(),
                exit = fadeOut() + shrinkVertically()
            ) {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .border(1.dp, BorderDark, RoundedCornerShape(16.dp)),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = CardDark)
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Text(
                            text = "Global Bot Settings",
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.Bold,
                            color = TextPrimary
                        )
                        ServerDropdown(
                            selectedServer = config.server,
                            enabled = !isRunning,
                            onServerSelected = onUpdateServer
                        )
                    }
                }
            }

            // 4. Tab Navigation (Accounts vs Logs)
            TabRow(
                selectedTabIndex = selectedTabIndex,
                containerColor = SurfaceDark,
                contentColor = TextPrimary,
                indicator = { tabPositions ->
                    if (selectedTabIndex < tabPositions.size) {
                        TabRowDefaults.SecondaryIndicator(
                            Modifier.tabIndicatorOffset(tabPositions[selectedTabIndex]),
                            color = DoomCrimson
                        )
                    }
                },
                divider = {},
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .border(1.dp, BorderDark, RoundedCornerShape(12.dp))
            ) {
                Tab(
                    selected = selectedTabIndex == 0,
                    onClick = { selectedTabIndex = 0 },
                    text = {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(6.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Filled.People,
                                contentDescription = null,
                                modifier = Modifier.size(16.dp),
                                tint = if (selectedTabIndex == 0) DoomCrimson else TextSecondary
                            )
                            Text(
                                text = "Accounts (${config.accounts.size})",
                                fontSize = 13.sp,
                                fontWeight = if (selectedTabIndex == 0) FontWeight.Bold else FontWeight.Medium,
                                color = if (selectedTabIndex == 0) TextPrimary else TextSecondary
                            )
                        }
                    }
                )
                Tab(
                    selected = selectedTabIndex == 1,
                    onClick = { selectedTabIndex = 1 },
                    text = {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(6.dp)
                        ) {
                            Icon(
                                imageVector = Icons.AutoMirrored.Filled.List,
                                contentDescription = null,
                                modifier = Modifier.size(16.dp),
                                tint = if (selectedTabIndex == 1) DoomCrimson else TextSecondary
                            )
                            Text(
                                text = "Live Logs (${logs.size})",
                                fontSize = 13.sp,
                                fontWeight = if (selectedTabIndex == 1) FontWeight.Bold else FontWeight.Medium,
                                color = if (selectedTabIndex == 1) TextPrimary else TextSecondary
                            )
                        }
                    }
                )
            }

            // 5. Tab Content: Accounts List or Logs Console (Isolated scroll areas)
            Box(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
            ) {
                when (selectedTabIndex) {
                    0 -> {
                        // Accounts Section: Pinned Header + Isolated Scrollable List
                        Column(
                            modifier = Modifier.fillMaxSize(),
                            verticalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            // Target Accounts Header & Add Button
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
                                            .clip(RoundedCornerShape(8.dp))
                                            .background(BorderDark)
                                            .padding(horizontal = 8.dp, vertical = 2.dp)
                                    ) {
                                        Text(
                                            text = "${config.accounts.count { it.enabled }} / ${config.accounts.size} selected",
                                            fontSize = 11.sp,
                                            fontWeight = FontWeight.Medium,
                                            color = TextSecondary
                                        )
                                    }
                                }

                                OutlinedButton(
                                    onClick = {
                                        editingAccount = null
                                        dialogUsername = ""
                                        dialogPassword = ""
                                        dialogPasswordVisible = false
                                        showAccountDialog = true
                                    },
                                    contentPadding = PaddingValues(
                                        horizontal = 10.dp,
                                        vertical = 8.dp
                                    ),
                                    shape = RoundedCornerShape(10.dp),
                                    border = BorderStroke(1.dp, DoomCrimson.copy(alpha = 0.5f)),
                                    colors = ButtonDefaults.outlinedButtonColors(contentColor = DoomCrimson)
                                ) {
                                    Icon(
                                        imageVector = Icons.Filled.Add,
                                        contentDescription = null,
                                        modifier = Modifier.size(16.dp)
                                    )
                                    Spacer(modifier = Modifier.width(6.dp))
                                    Text(
                                        text = "Add Account",
                                        fontSize = 12.sp,
                                        fontWeight = FontWeight.Bold
                                    )
                                }
                            }

                            // Accounts List (Compact, showing only username and results)
                            if (config.accounts.isEmpty()) {
                                Card(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .border(1.dp, BorderDark, RoundedCornerShape(16.dp)),
                                    shape = RoundedCornerShape(16.dp),
                                    colors = CardDefaults.cardColors(containerColor = CardDark)
                                ) {
                                    Column(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .padding(28.dp),
                                        horizontalAlignment = Alignment.CenterHorizontally,
                                        verticalArrangement = Arrangement.spacedBy(10.dp)
                                    ) {
                                        Icon(
                                            imageVector = Icons.Filled.Person,
                                            contentDescription = null,
                                            tint = TextMuted,
                                            modifier = Modifier.size(36.dp)
                                        )
                                        Text(
                                            text = "No accounts added yet",
                                            fontSize = 13.sp,
                                            fontWeight = FontWeight.SemiBold,
                                            color = TextPrimary
                                        )
                                        Text(
                                            text = "Tap '+ Add Account' above to configure an account.",
                                            fontSize = 11.sp,
                                            color = TextSecondary
                                        )
                                    }
                                }
                            } else {
                                val lazyListState = rememberLazyListState()
                                val reorderableLazyListState =
                                    rememberReorderableLazyListState(lazyListState) { from, to ->
                                        onMoveAccount(from.index, to.index)
                                    }

                                LazyColumn(
                                    state = lazyListState,
                                    modifier = Modifier
                                        .weight(1f)
                                        .fillMaxWidth(),
                                    verticalArrangement = Arrangement.spacedBy(12.dp),
                                    contentPadding = PaddingValues(bottom = 16.dp)
                                ) {
                                    items(config.accounts, key = { it.id }) { account ->
                                        ReorderableItem(
                                            reorderableLazyListState,
                                            key = account.id
                                        ) { isDragging ->
                                            val accTelemetry = telemetry.accounts[account.id]
                                            val accountIndex =
                                                config.accounts.indexOfFirst { it.id == account.id }
                                                    .let { if (it >= 0) it + 1 else 1 }
                                            DoomAccountCard(
                                                accountIndex = accountIndex,
                                                account = account,
                                                telemetry = accTelemetry,
                                                isBotRunning = isRunning,
                                                isDragging = isDragging,
                                                dragHandleModifier = Modifier.draggableHandle(
                                                    enabled = !isRunning
                                                ),
                                                onEdit = {
                                                    editingAccount = account
                                                    dialogUsername = account.username
                                                    dialogPassword = account.password
                                                    dialogPasswordVisible = false
                                                    showAccountDialog = true
                                                },
                                                onToggle = { enabled ->
                                                    onToggleAccount(
                                                        account.id,
                                                        enabled
                                                    )
                                                },
                                                onDelete = { accountToDelete = account }
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }

                    1 -> {
                        // Live Logs Tab (Isolated Scrollable Console)
                        LiveLogConsole(
                            logs = logs,
                            onClearLogs = onClearLogs,
                            title = "Weekly Doom Console",
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(bottom = 16.dp)
                        )
                    }
                }
            }
        }
    }

    // Add / Edit Account Popup Dialog
    if (showAccountDialog) {
        AlertDialog(
            onDismissRequest = { showAccountDialog = false },
            icon = {
                Icon(
                    imageVector = if (editingAccount == null) Icons.Filled.Person else Icons.Filled.Edit,
                    contentDescription = null,
                    tint = DoomCrimson
                )
            },
            title = {
                Text(
                    text = if (editingAccount == null) "Add Account" else "Edit Account",
                    fontWeight = FontWeight.Bold,
                    color = TextPrimary
                )
            },
            text = {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 8.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    OutlinedTextField(
                        value = dialogUsername,
                        onValueChange = { dialogUsername = it },
                        label = { Text("Username", fontSize = 11.sp) },
                        placeholder = { Text("Enter AQW username") },
                        leadingIcon = {
                            Icon(
                                imageVector = Icons.Filled.Person,
                                contentDescription = null,
                                tint = TextMuted,
                                modifier = Modifier.size(18.dp)
                            )
                        },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = DoomCrimson,
                            unfocusedBorderColor = BorderDark,
                            focusedTextColor = TextPrimary,
                            unfocusedTextColor = TextPrimary,
                            focusedLabelColor = DoomCrimson,
                            unfocusedLabelColor = TextMuted
                        ),
                        shape = RoundedCornerShape(10.dp)
                    )

                    OutlinedTextField(
                        value = dialogPassword,
                        onValueChange = { dialogPassword = it },
                        label = { Text("Password", fontSize = 11.sp) },
                        placeholder = { Text("Enter password") },
                        leadingIcon = {
                            Icon(
                                imageVector = Icons.Filled.Lock,
                                contentDescription = null,
                                tint = TextMuted,
                                modifier = Modifier.size(18.dp)
                            )
                        },
                        trailingIcon = {
                            IconButton(onClick = {
                                dialogPasswordVisible = !dialogPasswordVisible
                            }) {
                                Icon(
                                    imageVector = if (dialogPasswordVisible) Icons.Filled.Visibility else Icons.Filled.VisibilityOff,
                                    contentDescription = if (dialogPasswordVisible) "Hide Password" else "Show Password",
                                    tint = TextMuted,
                                    modifier = Modifier.size(18.dp)
                                )
                            }
                        },
                        visualTransformation = if (dialogPasswordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = DoomCrimson,
                            unfocusedBorderColor = BorderDark,
                            focusedTextColor = TextPrimary,
                            unfocusedTextColor = TextPrimary,
                            focusedLabelColor = DoomCrimson,
                            unfocusedLabelColor = TextMuted
                        ),
                        shape = RoundedCornerShape(10.dp)
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        val trimmedUser = dialogUsername.trim()
                        val trimmedPass = dialogPassword.trim()
                        if (trimmedUser.isNotBlank()) {
                            if (editingAccount == null) {
                                onAddAccount(trimmedUser, trimmedPass)
                            } else {
                                onUpdateAccount(
                                    editingAccount!!.id,
                                    trimmedUser,
                                    trimmedPass
                                )
                            }
                            showAccountDialog = false
                        }
                    },
                    enabled = dialogUsername.isNotBlank(),
                    colors = ButtonDefaults.buttonColors(containerColor = DoomCrimson)
                ) {
                    Text(if (editingAccount == null) "Add" else "Save")
                }
            },
            dismissButton = {
                TextButton(onClick = { showAccountDialog = false }) {
                    Text("Cancel", color = TextSecondary)
                }
            },
            containerColor = CardDark,
            shape = RoundedCornerShape(16.dp)
        )
    }

    // Delete Account Confirmation Dialog
    if (accountToDelete != null) {
        val targetAccount = accountToDelete!!
        AlertDialog(
            onDismissRequest = { accountToDelete = null },
            icon = {
                Icon(
                    imageVector = Icons.Filled.Warning,
                    contentDescription = null,
                    tint = ErrorRed
                )
            },
            title = {
                Text(
                    text = "Delete Account",
                    fontWeight = FontWeight.Bold,
                    color = TextPrimary
                )
            },
            text = {
                Text(
                    text = "Are you sure you want to remove '${if (targetAccount.username.isNotBlank()) targetAccount.username else "this account"}' from the target list?",
                    fontSize = 13.sp,
                    color = TextSecondary
                )
            },
            confirmButton = {
                Button(
                    onClick = {
                        onRemoveAccount(targetAccount.id)
                        accountToDelete = null
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = ErrorRed)
                ) {
                    Text("Delete", color = Color.White, fontWeight = FontWeight.Bold)
                }
            },
            dismissButton = {
                TextButton(onClick = { accountToDelete = null }) {
                    Text("Cancel", color = TextSecondary)
                }
            },
            containerColor = CardDark,
            shape = RoundedCornerShape(16.dp)
        )
    }
}

@Composable
fun WeeklyDoomStatsBar(
    isRunning: Boolean,
    telemetry: WeeklyDoomTelemetry,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .border(
                1.dp,
                if (isRunning) SuccessGreen.copy(alpha = 0.5f) else BorderDark,
                RoundedCornerShape(16.dp)
            ),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = CardDark)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 8.dp),
            verticalArrangement = Arrangement.spacedBy(2.dp)
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
                    Box(
                        modifier = Modifier
                            .size(8.dp)
                            .clip(CircleShape)
                            .background(if (isRunning) SuccessGreen else TextMuted)
                    )
                    Text(
                        text = if (isRunning) "RUNNER ACTIVE" else "RUNNER IDLE",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.ExtraBold,
                        color = if (isRunning) SuccessGreen else TextMuted
                    )
                }

                Text(
                    text = "Total: ${telemetry.totalAccounts} accounts",
                    fontSize = 11.sp,
                    color = TextMuted
                )
            }

            Text(
                text = if (isRunning && telemetry.currentUsername.isNotEmpty()) {
                    "Processing: ${telemetry.currentUsername} (${telemetry.currentIndex}/${telemetry.totalAccounts})"
                } else if (telemetry.completedAccounts > 0) {
                    "Finished ${telemetry.completedAccounts} / ${telemetry.totalAccounts} accounts"
                } else {
                    "Queued for automation"
                },
                fontSize = 12.sp,
                color = if (isRunning) MoonCyan else TextSecondary,
                fontWeight = FontWeight.Medium
            )
        }
    }
}

@Composable
fun WeeklyDoomActionControls(
    isRunning: Boolean,
    onStart: () -> Unit,
    onStop: () -> Unit,
    modifier: Modifier = Modifier
) {
    if (isRunning) {
        Button(
            onClick = onStop,
            modifier = modifier
                .fillMaxWidth()
                .height(48.dp),
            shape = RoundedCornerShape(12.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = ErrorRed,
                contentColor = Color.White
            )
        ) {
            Icon(
                imageVector = Icons.Filled.Stop,
                contentDescription = null,
                modifier = Modifier.size(20.dp)
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = "STOP WEEKLY DOOM BOT",
                fontSize = 13.sp,
                fontWeight = FontWeight.Bold
            )
        }
    } else {
        Button(
            onClick = onStart,
            modifier = modifier
                .fillMaxWidth()
                .height(48.dp),
            shape = RoundedCornerShape(12.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = SuccessGreen,
                contentColor = Color.White
            )
        ) {
            Icon(
                imageVector = Icons.Filled.PlayArrow,
                contentDescription = null,
                modifier = Modifier.size(20.dp)
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = "START WEEKLY DOOM BOT",
                fontSize = 13.sp,
                fontWeight = FontWeight.Bold
            )
        }
    }
}

@Composable
fun DoomAccountCard(
    accountIndex: Int,
    account: DoomAccount,
    telemetry: DoomAccountTelemetry?,
    isBotRunning: Boolean,
    isDragging: Boolean = false,
    dragHandleModifier: Modifier = Modifier,
    onEdit: () -> Unit,
    onToggle: (Boolean) -> Unit,
    onDelete: () -> Unit,
    modifier: Modifier = Modifier
) {
    val status = telemetry?.status ?: if (account.enabled) "Idle" else "Disabled"
    val statusColor = when (status.lowercase()) {
        "running" -> MoonCyan
        "finished", "completed" -> SuccessGreen
        "not enough gear" -> SunGold
        "failed", "error" -> ErrorRed
        "pending" -> PrimaryPurple
        else -> TextMuted
    }

    Card(
        modifier = modifier
            .fillMaxWidth()
            .border(
                1.dp,
                when {
                    isDragging -> DoomCrimson
                    status.equals("Running", ignoreCase = true) -> MoonCyan.copy(alpha = 0.6f)
                    else -> BorderDark
                },
                RoundedCornerShape(16.dp)
            ),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = if (isDragging) CardDark.copy(alpha = 0.95f) else CardDark
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Main Row: Index + Username & Status + Actions (Switch, Edit, Delete)
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(
                    modifier = Modifier.weight(1f),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    // Drag Handle
                    Box(
                        modifier = Modifier
                            .size(32.dp)
                            .clip(RoundedCornerShape(8.dp))
                            .background(if (isDragging) DoomCrimson.copy(alpha = 0.2f) else Color.Transparent)
                            .then(dragHandleModifier),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = Icons.Filled.DragHandle,
                            contentDescription = "Drag to reorder",
                            tint = if (isDragging) DoomCrimson else if (!isBotRunning) TextSecondary else TextMuted.copy(
                                alpha = 0.3f
                            ),
                            modifier = Modifier.size(20.dp)
                        )
                    }

                    Box(
                        modifier = Modifier
                            .size(28.dp)
                            .clip(CircleShape)
                            .background(if (isDragging) DoomCrimson.copy(alpha = 0.2f) else BorderDark),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "$accountIndex",
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (isDragging) DoomCrimson else TextPrimary
                        )
                    }

                    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Text(
                            text = if (account.username.isNotBlank()) account.username else "Account #$accountIndex",
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.Bold,
                            color = TextPrimary
                        )
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(4.dp)
                        ) {
                            Box(
                                modifier = Modifier
                                    .size(6.dp)
                                    .clip(CircleShape)
                                    .background(statusColor)
                            )
                            Text(
                                text = status,
                                fontSize = 11.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = statusColor
                            )
                        }
                    }
                }

                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    Switch(
                        checked = account.enabled,
                        onCheckedChange = { onToggle(it) },
                        enabled = !isBotRunning,
                        colors = SwitchDefaults.colors(
                            checkedThumbColor = SuccessGreen,
                            checkedTrackColor = SuccessGreen.copy(alpha = 0.3f),
                            uncheckedThumbColor = TextMuted,
                            uncheckedTrackColor = BorderDark
                        )
                    )
                    IconButton(
                        onClick = onEdit,
                        enabled = !isBotRunning,
                        modifier = Modifier.size(32.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Filled.Edit,
                            contentDescription = "Edit Account",
                            tint = if (isBotRunning) TextMuted.copy(alpha = 0.5f) else TextSecondary,
                            modifier = Modifier.size(17.dp)
                        )
                    }
                    IconButton(
                        onClick = onDelete,
                        enabled = !isBotRunning,
                        modifier = Modifier.size(32.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Filled.Delete,
                            contentDescription = "Delete Account",
                            tint = if (isBotRunning) TextMuted.copy(alpha = 0.5f) else TextMuted,
                            modifier = Modifier.size(17.dp)
                        )
                    }
                }
            }

            // Result / Message Details (if any)
            if (telemetry != null && telemetry.message.isNotBlank() && telemetry.message != "Waiting in queue..." && telemetry.message != "Disabled") {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(SurfaceDark.copy(alpha = 0.6f))
                        .padding(horizontal = 10.dp, vertical = 6.dp)
                ) {
                    Text(
                        text = "Result: ${telemetry.message}",
                        fontSize = 11.sp,
                        color = when (status.lowercase()) {
                            "finished", "completed" -> SuccessGreen
                            "not enough gear" -> SunGold
                            "failed", "error" -> ErrorRed
                            else -> TextSecondary
                        },
                        fontWeight = FontWeight.Medium
                    )
                }
            }

            // Wheel Drops Badge (if any)
            if (telemetry != null && telemetry.wheelDrops.isNotEmpty()) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(SuccessGreen.copy(alpha = 0.12f))
                        .padding(horizontal = 10.dp, vertical = 6.dp)
                ) {
                    Text(
                        text = "Won: ${telemetry.wheelDrops.joinToString(", ")}",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Medium,
                        color = SuccessGreen
                    )
                }
            }

            // EIODA Special Banner (if dropped)
            if (telemetry?.hasEioda == true) {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .border(1.dp, DoomGold, RoundedCornerShape(8.dp)),
                    shape = RoundedCornerShape(8.dp),
                    colors = CardDefaults.cardColors(containerColor = DoomGold.copy(alpha = 0.15f))
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 10.dp, vertical = 6.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(6.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Filled.Star,
                            contentDescription = null,
                            tint = DoomGold,
                            modifier = Modifier.size(16.dp)
                        )
                        Text(
                            text = "★ Epic Item of Digital Awesomeness in Inventory!",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = DoomGold
                        )
                    }
                }
            }
        }
    }
}

// =========================================================================
// Previews
// =========================================================================

@Preview(showBackground = true, backgroundColor = 0xFF0B0D14)
@Composable
private fun WeeklyDoomContentIdlePreview() {
    MyApplicationTheme {
        WeeklyDoomContent(
            config = WeeklyDoomConfig(
                server = "Alteon",
                accounts = listOf(
                    DoomAccount(id = "1", username = "ShadowSlayer", enabled = true),
                    DoomAccount(id = "2", username = "DoomKnight99", enabled = true),
                    DoomAccount(id = "3", username = "HeroOfLore", enabled = false)
                )
            ),
            telemetry = WeeklyDoomTelemetry(
                running = false,
                totalAccounts = 3,
                completedAccounts = 0
            ),
            logs = emptyList(),
            isRunning = false,
            onBack = {},
            onStart = {},
            onStop = {},
            onUpdateServer = {},
            onAddAccount = { _, _ -> },
            onUpdateAccount = { _, _, _ -> },
            onToggleAccount = { _, _ -> },
            onRemoveAccount = {},
            onMoveAccount = { _, _ -> },
            onClearLogs = {}
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF0B0D14)
@Composable
private fun WeeklyDoomContentRunningPreview() {
    MyApplicationTheme {
        WeeklyDoomContent(
            config = WeeklyDoomConfig(
                server = "Alteon",
                accounts = listOf(
                    DoomAccount(id = "1", username = "ShadowSlayer", enabled = true),
                    DoomAccount(id = "2", username = "DoomKnight99", enabled = true),
                    DoomAccount(id = "3", username = "HeroOfLore", enabled = true)
                )
            ),
            telemetry = WeeklyDoomTelemetry(
                running = true,
                currentIndex = 2,
                currentUsername = "DoomKnight99",
                totalAccounts = 3,
                completedAccounts = 1,
                timeRunning = 145L,
                accounts = mapOf(
                    "1" to DoomAccountTelemetry(
                        id = "1",
                        username = "ShadowSlayer",
                        status = "Completed",
                        message = "Spin completed. 2 items received.",
                        hasEioda = true,
                        wheelDrops = listOf("Doom Blade of Chaos", "1,000 Gold")
                    ),
                    "2" to DoomAccountTelemetry(
                        id = "2",
                        username = "DoomKnight99",
                        status = "Running",
                        message = "Spinning Wheel of Doom..."
                    ),
                    "3" to DoomAccountTelemetry(
                        id = "3",
                        username = "HeroOfLore",
                        status = "Idle",
                        message = "Waiting in queue..."
                    )
                )
            ),
            logs = emptyList(),
            isRunning = true,
            onBack = {},
            onStart = {},
            onStop = {},
            onUpdateServer = {},
            onAddAccount = { _, _ -> },
            onUpdateAccount = { _, _, _ -> },
            onToggleAccount = { _, _ -> },
            onRemoveAccount = {},
            onMoveAccount = { _, _ -> },
            onClearLogs = {}
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF0B0D14)
@Composable
private fun WeeklyDoomContentLogsPreview() {
    MyApplicationTheme {
        WeeklyDoomContent(
            config = WeeklyDoomConfig(
                server = "Alteon",
                accounts = listOf(
                    DoomAccount(id = "1", username = "ShadowSlayer", enabled = true)
                )
            ),
            telemetry = WeeklyDoomTelemetry(
                running = true,
                currentIndex = 1,
                currentUsername = "ShadowSlayer",
                totalAccounts = 1,
                completedAccounts = 0
            ),
            logs = listOf(
                LogEntry(
                    botType = "weekly_doom",
                    username = "ShadowSlayer",
                    message = "Connecting to Alteon server..."
                ),
                LogEntry(
                    botType = "weekly_doom",
                    username = "ShadowSlayer",
                    message = "Connected and logged in successfully"
                ),
                LogEntry(
                    botType = "weekly_doom",
                    username = "ShadowSlayer",
                    message = "Spinning Wheel of Doom..."
                ),
                LogEntry(
                    botType = "weekly_doom",
                    username = "ShadowSlayer",
                    message = "Wheel drop: Doom Blade of Chaos"
                ),
                LogEntry(
                    botType = "weekly_doom",
                    username = "ShadowSlayer",
                    message = "Spin completed successfully"
                )
            ),
            isRunning = true,
            initialTabIndex = 1,
            onBack = {},
            onStart = {},
            onStop = {},
            onUpdateServer = {},
            onAddAccount = { _, _ -> },
            onUpdateAccount = { _, _, _ -> },
            onToggleAccount = { _, _ -> },
            onRemoveAccount = {},
            onMoveAccount = { _, _ -> },
            onClearLogs = {}
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF0B0D14)
@Composable
private fun WeeklyDoomContentSettingsPreview() {
    MyApplicationTheme {
        WeeklyDoomContent(
            config = WeeklyDoomConfig(
                server = "Alteon",
                accounts = listOf(
                    DoomAccount(id = "1", username = "ShadowSlayer", enabled = true)
                )
            ),
            telemetry = WeeklyDoomTelemetry(),
            logs = emptyList(),
            isRunning = false,
            initialShowSettings = true,
            onBack = {},
            onStart = {},
            onStop = {},
            onUpdateServer = {},
            onAddAccount = { _, _ -> },
            onUpdateAccount = { _, _, _ -> },
            onToggleAccount = { _, _ -> },
            onRemoveAccount = {},
            onMoveAccount = { _, _ -> },
            onClearLogs = {}
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF0B0D14)
@Composable
private fun WeeklyDoomContentEmptyPreview() {
    MyApplicationTheme {
        WeeklyDoomContent(
            config = WeeklyDoomConfig(
                server = "Alteon",
                accounts = emptyList()
            ),
            telemetry = WeeklyDoomTelemetry(
                running = false,
                totalAccounts = 0,
                completedAccounts = 0
            ),
            logs = emptyList(),
            isRunning = false,
            onBack = {},
            onStart = {},
            onStop = {},
            onUpdateServer = {},
            onAddAccount = { _, _ -> },
            onUpdateAccount = { _, _, _ -> },
            onToggleAccount = { _, _ -> },
            onRemoveAccount = {},
            onMoveAccount = { _, _ -> },
            onClearLogs = {}
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF0B0D14)
@Composable
private fun DoomAccountCardPreview() {
    MyApplicationTheme {
        DoomAccountCard(
            accountIndex = 1,
            account = DoomAccount(username = "ShadowSlayer", enabled = true),
            telemetry = DoomAccountTelemetry(
                status = "Finished",
                message = "2 rewards dropped",
                hasEioda = true,
                wheelDrops = listOf("Doom Blade of Chaos", "1,000 Gold")
            ),
            isBotRunning = false,
            onEdit = {},
            onToggle = {},
            onDelete = {},
            modifier = Modifier.padding(16.dp)
        )
    }
}
