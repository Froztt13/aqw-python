package froztt13.python.aqw.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.PaddingValues
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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.DragHandle
import androidx.compose.material.icons.filled.Explore
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Refresh
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
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.MenuAnchorType
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import froztt13.python.aqw.data.SlaveryConfig
import froztt13.python.aqw.ui.components.CustomOutlinedTextField
import froztt13.python.aqw.ui.components.ServerDropdown
import froztt13.python.aqw.ui.theme.BgDark
import froztt13.python.aqw.ui.theme.CardDark
import froztt13.python.aqw.ui.theme.ErrorRed
import froztt13.python.aqw.ui.theme.MyApplicationTheme
import froztt13.python.aqw.ui.theme.SlaveIndigo
import froztt13.python.aqw.ui.theme.TextMuted
import froztt13.python.aqw.ui.theme.TextPrimary
import froztt13.python.aqw.ui.theme.TextSecondary
import sh.calvin.reorderable.ReorderableColumn

val DEFAULT_LOCKED_ZONES = listOf(
    "ultraezrajal",
    "ultrawarden",
    "ultraengineer",
    "doomvault",
    "doomvaultb",
    "championdrakath",
    "tercessuinotlim",
    "icestormunder"
)

val POPULAR_LOCKED_ZONE_SUGGESTIONS = listOf(
    "ultraezrajal",
    "ultrawarden",
    "ultraengineer",
    "ultratyndarius",
    "championdrakath",
    "ultradarkon",
    "ultradage",
    "doomvault",
    "doomvaultb",
    "tercessuinotlim",
    "icestormunder"
)

@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class)
@Composable
fun SlaverySettingsScreen(
    config: SlaveryConfig,
    isRunning: Boolean,
    onBack: () -> Unit,
    onUpdateGlobalSettings: (
        server: String,
        followPlayer: String,
        defaultRoomNumber: Int,
        copyWalk: Boolean,
        autoZone: String,
        targetsPriority: String,
        whitelist: String,
        lockedZones: List<String>
    ) -> Unit,
    onResetSettings: () -> Unit,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()
    val themeColor = SlaveIndigo
    var showResetConfirmDialog by remember { mutableStateOf(false) }
    var newMapInput by remember { mutableStateOf("") }

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
                        IconButton(onClick = onBack) {
                            Icon(
                                imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                                contentDescription = "Back to Main",
                                tint = TextPrimary
                            )
                        }
                        Text(
                            text = "Global Slavery Settings",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = TextPrimary
                        )
                    }
                },
                actions = {
                    IconButton(
                        onClick = { showResetConfirmDialog = true },
                        enabled = !isRunning
                    ) {
                        Icon(
                            imageVector = Icons.Filled.Refresh,
                            contentDescription = "Reset Settings",
                            tint = if (!isRunning) TextSecondary else TextMuted
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
            // 1. Master Account & Movement Mimicking Card
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, Color(0xFF2E3350), RoundedCornerShape(14.dp)),
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = CardDark)
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(14.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Text(
                        text = "Master Account & Movement",
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Bold,
                        color = themeColor
                    )

                    CustomOutlinedTextField(
                        value = config.followPlayer,
                        onValueChange = {
                            onUpdateGlobalSettings(
                                config.server,
                                it,
                                config.defaultRoomNumber,
                                config.copyWalk,
                                config.autoZone,
                                config.targetsPriority,
                                config.whitelist,
                                config.lockedZones
                            )
                        },
                        label = { Text("Master Account to Follow") },
                        placeholder = { Text("e.g. MasterPlayer", color = TextMuted) },
                        leadingIcon = {
                            Icon(
                                imageVector = Icons.Filled.Person,
                                contentDescription = null,
                                tint = themeColor
                            )
                        },
                        singleLine = true,
                        enabled = !isRunning,
                        modifier = Modifier.fillMaxWidth(),
                        contentPadding = PaddingValues(horizontal = 14.dp, vertical = 10.dp),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = themeColor,
                            unfocusedBorderColor = Color(0xFF334155),
                            focusedTextColor = TextPrimary,
                            unfocusedTextColor = TextPrimary
                        )
                    )

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
                                text = "Mimic Movement (Copy Walk)",
                                fontSize = 13.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = TextPrimary
                            )
                            Text(
                                text = "Copy walk coordinates from Master",
                                fontSize = 11.sp,
                                color = TextSecondary
                            )
                        }
                        Switch(
                            checked = config.copyWalk,
                            onCheckedChange = {
                                onUpdateGlobalSettings(
                                    config.server,
                                    config.followPlayer,
                                    config.defaultRoomNumber,
                                    it,
                                    config.autoZone,
                                    config.targetsPriority,
                                    config.whitelist,
                                    config.lockedZones
                                )
                            },
                            enabled = !isRunning,
                            colors = SwitchDefaults.colors(
                                checkedThumbColor = Color.White,
                                checkedTrackColor = themeColor,
                                uncheckedThumbColor = Color(0xFF94A3B8),
                                uncheckedTrackColor = Color(0xFF334155)
                            )
                        )
                    }
                }
            }

            // 2. Server & Room Settings Card
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, Color(0xFF2E3350), RoundedCornerShape(14.dp)),
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = CardDark)
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(14.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Text(
                        text = "Connection & Room",
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Bold,
                        color = themeColor
                    )

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        ServerDropdown(
                            selectedServer = config.server,
                            enabled = !isRunning,
                            onServerSelected = {
                                onUpdateGlobalSettings(
                                    it,
                                    config.followPlayer,
                                    config.defaultRoomNumber,
                                    config.copyWalk,
                                    config.autoZone,
                                    config.targetsPriority,
                                    config.whitelist,
                                    config.lockedZones
                                )
                            },
                            contentPadding = PaddingValues(horizontal = 14.dp, vertical = 10.dp),
                            modifier = Modifier.weight(1f)
                        )

                        CustomOutlinedTextField(
                            value = config.defaultRoomNumber.toString(),
                            onValueChange = {
                                val num = it.toIntOrNull() ?: 9099
                                onUpdateGlobalSettings(
                                    config.server,
                                    config.followPlayer,
                                    num,
                                    config.copyWalk,
                                    config.autoZone,
                                    config.targetsPriority,
                                    config.whitelist,
                                    config.lockedZones
                                )
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
                }
            }

            // 3. Combat & Boss Mechanics Card
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, Color(0xFF2E3350), RoundedCornerShape(14.dp)),
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = CardDark)
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(14.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Text(
                        text = "Combat & Mechanics",
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Bold,
                        color = themeColor
                    )

                    var autoZoneExpanded by remember { mutableStateOf(false) }
                    ExposedDropdownMenuBox(
                        expanded = autoZoneExpanded && !isRunning,
                        onExpandedChange = {
                            if (!isRunning) autoZoneExpanded = !autoZoneExpanded
                        },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        CustomOutlinedTextField(
                            value = config.autoZone,
                            onValueChange = {},
                            readOnly = true,
                            label = { Text("Boss Auto Zone Mechanics") },
                            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = autoZoneExpanded) },
                            enabled = !isRunning,
                            modifier = Modifier
                                .menuAnchor(MenuAnchorType.PrimaryNotEditable, true)
                                .fillMaxWidth(),
                            contentPadding = PaddingValues(horizontal = 14.dp, vertical = 10.dp),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = themeColor,
                                unfocusedBorderColor = Color(0xFF334155),
                                focusedTextColor = TextPrimary,
                                unfocusedTextColor = TextPrimary
                            )
                        )

                        ExposedDropdownMenu(
                            expanded = autoZoneExpanded && !isRunning,
                            onDismissRequest = { autoZoneExpanded = false },
                            modifier = Modifier.background(CardDark)
                        ) {
                            AUTO_ZONE_OPTIONS.forEach { zoneName ->
                                DropdownMenuItem(
                                    text = { Text(text = zoneName, color = TextPrimary) },
                                    onClick = {
                                        onUpdateGlobalSettings(
                                            config.server,
                                            config.followPlayer,
                                            config.defaultRoomNumber,
                                            config.copyWalk,
                                            zoneName,
                                            config.targetsPriority,
                                            config.whitelist,
                                            config.lockedZones
                                        )
                                        autoZoneExpanded = false
                                    }
                                )
                            }
                        }
                    }

                    CustomOutlinedTextField(
                        value = config.targetsPriority,
                        onValueChange = {
                            onUpdateGlobalSettings(
                                config.server,
                                config.followPlayer,
                                config.defaultRoomNumber,
                                config.copyWalk,
                                config.autoZone,
                                it,
                                config.whitelist,
                                config.lockedZones
                            )
                        },
                        label = { Text("Priority Targets (Comma-Separated)") },
                        placeholder = {
                            Text(
                                "e.g. Defense Drone,Staff of Inversion",
                                color = TextMuted
                            )
                        },
                        singleLine = true,
                        enabled = !isRunning,
                        modifier = Modifier.fillMaxWidth(),
                        contentPadding = PaddingValues(horizontal = 14.dp, vertical = 10.dp),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = themeColor,
                            unfocusedBorderColor = Color(0xFF334155),
                            focusedTextColor = TextPrimary,
                            unfocusedTextColor = TextPrimary
                        )
                    )

                    CustomOutlinedTextField(
                        value = config.whitelist,
                        onValueChange = {
                            onUpdateGlobalSettings(
                                config.server,
                                config.followPlayer,
                                config.defaultRoomNumber,
                                config.copyWalk,
                                config.autoZone,
                                config.targetsPriority,
                                it,
                                config.lockedZones
                            )
                        },
                        label = { Text("Item Drops Whitelist") },
                        placeholder = {
                            Text(
                                "e.g. Treasure Chest, Void Aura",
                                color = TextMuted
                            )
                        },
                        singleLine = true,
                        enabled = !isRunning,
                        modifier = Modifier.fillMaxWidth(),
                        contentPadding = PaddingValues(horizontal = 14.dp, vertical = 10.dp),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = themeColor,
                            unfocusedBorderColor = Color(0xFF334155),
                            focusedTextColor = TextPrimary,
                            unfocusedTextColor = TextPrimary
                        )
                    )
                }
            }

            // 4. Locked Zone Search Maps Card (List View)
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, Color(0xFF2E3350), RoundedCornerShape(14.dp)),
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = CardDark)
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(14.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text(
                                text = "Locked Zone Search Maps",
                                fontSize = 13.sp,
                                fontWeight = FontWeight.Bold,
                                color = themeColor
                            )
                            Text(
                                text = "Maps to sequentially check when master cannot be reached",
                                fontSize = 11.sp,
                                color = TextSecondary
                            )
                        }
                    }

                    // Input to add new Map
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(IntrinsicSize.Max),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        CustomOutlinedTextField(
                            value = newMapInput,
                            onValueChange = { newMapInput = it },
                            label = { Text("Add Map Name") },
                            placeholder = { Text("e.g. ultrawarden", color = TextMuted) },
                            singleLine = true,
                            enabled = !isRunning,
                            modifier = Modifier.weight(1f),
                            keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
                            keyboardActions = KeyboardActions(onDone = {
                                val trimmed = newMapInput.trim().lowercase()
                                if (trimmed.isNotEmpty() && !config.lockedZones.contains(trimmed)) {
                                    onUpdateGlobalSettings(
                                        config.server,
                                        config.followPlayer,
                                        config.defaultRoomNumber,
                                        config.copyWalk,
                                        config.autoZone,
                                        config.targetsPriority,
                                        config.whitelist,
                                        config.lockedZones + trimmed
                                    )
                                    newMapInput = ""
                                }
                            }),
                            contentPadding = PaddingValues(horizontal = 12.dp, vertical = 10.dp),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = themeColor,
                                unfocusedBorderColor = Color(0xFF334155),
                                focusedTextColor = TextPrimary,
                                unfocusedTextColor = TextPrimary
                            )
                        )

                        Button(
                            onClick = {
                                val trimmed = newMapInput.trim().lowercase()
                                if (trimmed.isNotEmpty() && !config.lockedZones.contains(trimmed)) {
                                    onUpdateGlobalSettings(
                                        config.server,
                                        config.followPlayer,
                                        config.defaultRoomNumber,
                                        config.copyWalk,
                                        config.autoZone,
                                        config.targetsPriority,
                                        config.whitelist,
                                        config.lockedZones + trimmed
                                    )
                                    newMapInput = ""
                                }
                            },
                            enabled = !isRunning && newMapInput.isNotBlank(),
                            shape = RoundedCornerShape(8.dp),
                            modifier = Modifier.fillMaxHeight(),
                            colors = ButtonDefaults.buttonColors(containerColor = themeColor)
                        ) {
                            Icon(
                                imageVector = Icons.Filled.Add,
                                contentDescription = "Add Map",
                                tint = Color.White
                            )
                        }
                    }

                    // Interactive List of Maps
                    if (config.lockedZones.isEmpty()) {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clip(RoundedCornerShape(8.dp))
                                .background(Color(0xFF161928))
                                .padding(12.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = "No locked zone maps configured. Add maps above.",
                                fontSize = 11.sp,
                                color = TextMuted
                            )
                        }
                    } else {
                        ReorderableColumn(
                            list = config.lockedZones,
                            onSettle = { fromIndex, toIndex ->
                                val updatedList = config.lockedZones.toMutableList()
                                val item = updatedList.removeAt(fromIndex)
                                updatedList.add(toIndex, item)
                                onUpdateGlobalSettings(
                                    config.server,
                                    config.followPlayer,
                                    config.defaultRoomNumber,
                                    config.copyWalk,
                                    config.autoZone,
                                    config.targetsPriority,
                                    config.whitelist,
                                    updatedList
                                )
                            },
                            verticalArrangement = Arrangement.spacedBy(6.dp),
                            modifier = Modifier.fillMaxWidth()
                        ) { index, mapName, isDragging ->
                            key(mapName) {
                                val borderColor = if (isDragging) themeColor else Color(0xFF2E3350)
                                val cardBg =
                                    if (isDragging) Color(0xFF222842) else Color(0xFF161928)

                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .clip(RoundedCornerShape(8.dp))
                                        .background(cardBg)
                                        .border(
                                            width = if (isDragging) 1.5.dp else 1.dp,
                                            color = borderColor,
                                            shape = RoundedCornerShape(8.dp)
                                        )
                                        .padding(horizontal = 10.dp, vertical = 8.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Row(
                                        verticalAlignment = Alignment.CenterVertically,
                                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                                        modifier = Modifier.weight(1f)
                                    ) {
                                        // Drag Handle
                                        Box(
                                            modifier = Modifier
                                                .size(28.dp)
                                                .clip(RoundedCornerShape(6.dp))
                                                .background(
                                                    if (isDragging) themeColor.copy(alpha = 0.25f)
                                                    else Color(0xFF1E2235)
                                                )
                                                .draggableHandle(enabled = !isRunning),
                                            contentAlignment = Alignment.Center
                                        ) {
                                            Icon(
                                                imageVector = Icons.Filled.DragHandle,
                                                contentDescription = "Drag to reorder",
                                                tint = if (isDragging) Color.White else TextMuted,
                                                modifier = Modifier.size(16.dp)
                                            )
                                        }

                                        Text(
                                            text = "#${index + 1}",
                                            fontSize = 11.sp,
                                            fontWeight = FontWeight.Bold,
                                            color = TextMuted,
                                            modifier = Modifier.width(24.dp)
                                        )
                                        Icon(
                                            imageVector = Icons.Filled.Explore,
                                            contentDescription = null,
                                            tint = themeColor,
                                            modifier = Modifier.size(16.dp)
                                        )
                                        Text(
                                            text = mapName,
                                            fontSize = 12.sp,
                                            fontWeight = FontWeight.SemiBold,
                                            color = TextPrimary
                                        )
                                    }

                                    if (!isRunning) {
                                        IconButton(
                                            onClick = {
                                                val updatedList =
                                                    config.lockedZones.toMutableList().apply {
                                                        removeAt(index)
                                                    }
                                                onUpdateGlobalSettings(
                                                    config.server,
                                                    config.followPlayer,
                                                    config.defaultRoomNumber,
                                                    config.copyWalk,
                                                    config.autoZone,
                                                    config.targetsPriority,
                                                    config.whitelist,
                                                    updatedList
                                                )
                                            },
                                            modifier = Modifier.size(24.dp)
                                        ) {
                                            Icon(
                                                imageVector = Icons.Filled.Close,
                                                contentDescription = "Remove map",
                                                tint = ErrorRed.copy(alpha = 0.8f),
                                                modifier = Modifier.size(14.dp)
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // Suggestions row if any common maps are missing
                    val missingSuggestions = POPULAR_LOCKED_ZONE_SUGGESTIONS.filter {
                        !config.lockedZones.contains(it)
                    }
                    if (missingSuggestions.isNotEmpty() && !isRunning) {
                        Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                            Text(
                                text = "Quick Add Popular Ultra Maps:",
                                fontSize = 10.sp,
                                color = TextMuted
                            )
                            FlowRow(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(6.dp),
                                verticalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                missingSuggestions.take(6).forEach { suggestion ->
                                    Box(
                                        modifier = Modifier
                                            .clip(RoundedCornerShape(6.dp))
                                            .background(Color(0xFF1E2338))
                                            .border(
                                                0.5.dp,
                                                Color(0xFF333B58),
                                                RoundedCornerShape(6.dp)
                                            )
                                            .clickable {
                                                onUpdateGlobalSettings(
                                                    config.server,
                                                    config.followPlayer,
                                                    config.defaultRoomNumber,
                                                    config.copyWalk,
                                                    config.autoZone,
                                                    config.targetsPriority,
                                                    config.whitelist,
                                                    config.lockedZones + suggestion
                                                )
                                            }
                                            .padding(horizontal = 8.dp, vertical = 4.dp)
                                    ) {
                                        Text(
                                            text = "+ $suggestion",
                                            fontSize = 10.sp,
                                            color = TextSecondary
                                        )
                                    }
                                }
                            }
                        }
                    }

                    // Reset Maps to Defaults
                    if (!isRunning) {
                        TextButton(
                            onClick = {
                                onUpdateGlobalSettings(
                                    config.server,
                                    config.followPlayer,
                                    config.defaultRoomNumber,
                                    config.copyWalk,
                                    config.autoZone,
                                    config.targetsPriority,
                                    config.whitelist,
                                    DEFAULT_LOCKED_ZONES
                                )
                            },
                            modifier = Modifier.align(Alignment.End)
                        ) {
                            Text("Reset Maps to Default", fontSize = 11.sp, color = TextSecondary)
                        }
                    }
                }
            }

            // 5. Reset All Settings Button
            OutlinedButton(
                onClick = { showResetConfirmDialog = true },
                enabled = !isRunning,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(44.dp),
                shape = RoundedCornerShape(10.dp),
                border = BorderStroke(1.dp, Color(0xFF4A202A)),
                colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFFF87171))
            ) {
                Icon(
                    imageVector = Icons.Filled.Refresh,
                    contentDescription = null,
                    modifier = Modifier.size(16.dp),
                    tint = Color(0xFFF87171)
                )
                Spacer(Modifier.width(8.dp))
                Text(
                    text = "Reset All Settings to Default",
                    fontSize = 12.sp,
                    fontWeight = FontWeight.SemiBold
                )
            }

            Spacer(modifier = Modifier.height(24.dp))
        }
    }

    // Reset Confirm Dialog
    if (showResetConfirmDialog) {
        AlertDialog(
            onDismissRequest = { showResetConfirmDialog = false },
            icon = {
                Icon(
                    imageVector = Icons.Filled.Warning,
                    contentDescription = null,
                    tint = ErrorRed,
                    modifier = Modifier.size(28.dp)
                )
            },
            title = {
                Text(
                    text = "Reset Global Settings?",
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
            },
            text = {
                Text(
                    text = "This will restore server, default room, follow player, locked zone maps, and targets back to default values. Slot accounts will NOT be deleted.",
                    fontSize = 13.sp,
                    color = TextSecondary
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
                    Text("Reset All", color = Color.White)
                }
            },
            dismissButton = {
                TextButton(onClick = { showResetConfirmDialog = false }) {
                    Text("Cancel", color = TextSecondary)
                }
            },
            containerColor = Color(0xFF1E2235),
            shape = RoundedCornerShape(14.dp)
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF0B0D14)
@Composable
private fun SlaverySettingsScreenPreview() {
    MyApplicationTheme {
        SlaverySettingsScreen(
            config = SlaveryConfig(
                server = "Gravelyn",
                followPlayer = "MasterPlayer",
                defaultRoomNumber = 9099,
                copyWalk = true,
                autoZone = "Astral Empyrean",
                targetsPriority = "Defense Drone,Staff of Inversion",
                whitelist = "Scroll of Enrage,Treasure Chest",
                lockedZones = listOf("ultraezrajal", "ultrawarden", "ultraengineer", "doomvault")
            ),
            isRunning = false,
            onBack = {},
            onUpdateGlobalSettings = { _, _, _, _, _, _, _, _ -> },
            onResetSettings = {}
        )
    }
}
