package froztt13.python.aqw.ui.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.BatteryAlert
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.Timer
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
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
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.MenuAnchorType
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import froztt13.python.aqw.data.LogEntry
import froztt13.python.aqw.data.MonsterTelemetry
import froztt13.python.aqw.data.PartyStats
import froztt13.python.aqw.data.SlotConfig
import froztt13.python.aqw.data.SlotTelemetry
import froztt13.python.aqw.ui.theme.CardDark
import froztt13.python.aqw.ui.theme.ErrorRed
import froztt13.python.aqw.ui.theme.MoonCyan
import froztt13.python.aqw.ui.theme.MyApplicationTheme
import froztt13.python.aqw.ui.theme.PrimaryPurple
import froztt13.python.aqw.ui.theme.SuccessGreen
import froztt13.python.aqw.ui.theme.SunGold
import froztt13.python.aqw.ui.theme.TextMuted
import froztt13.python.aqw.ui.theme.TextPrimary
import froztt13.python.aqw.ui.theme.TextSecondary

val AQW_CLASS_OPTIONS = listOf(
    "ArchPaladin",
    "StoneCrusher",
    "Lord of Order",
    "Legion Revenant",
    "Dragon of Time",
    "Void Highlord",
    "Chaos Avenger",
    "LightCaster",
)

val SERVER_OPTIONS = listOf(
    "Alteon",
    "Artix",
    "Gravelyn",
    "Safiria",
    "Twilly",
    "Yorumi"
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SlotCard(
    modifier: Modifier = Modifier,
    slotKey: String,
    title: String,
    config: SlotConfig,
    telemetry: SlotTelemetry,
    isPartyRunning: Boolean,
    accentColor: Color = PrimaryPurple,
    showTauntToggle: Boolean = true,
    showEclipseTauntToggles: Boolean = false,
    onConfigChange: (SlotConfig) -> Unit
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
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Header Row: Title, Role Badge, Status
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
                            .background(if (telemetry.running) SuccessGreen else Color(0xFF64748B))
                    )
                    Text(
                        text = title,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = TextPrimary
                    )
                }

                Row(
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
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
                }
            }

            // Real-time Telemetry (when party is running)
            AnimatedVisibility(visible = telemetry.running) {
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

                    // Target Monsters (Active / Default)
                    val activeTarget = telemetry.targetMonsters.ifEmpty { config.defaultTarget }
                    if (activeTarget.isNotEmpty()) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clip(RoundedCornerShape(6.dp))
                                .background(Color(0xFF161928))
                                .padding(horizontal = 8.dp, vertical = 5.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(6.dp),
                                modifier = Modifier.weight(1f, fill = false)
                            ) {
                                Box(
                                    modifier = Modifier
                                        .size(6.dp)
                                        .clip(CircleShape)
                                        .background(accentColor)
                                )
                                Text(
                                    text = "Target Monsters",
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Medium,
                                    color = TextSecondary
                                )
                            }
                            Spacer(modifier = Modifier.size(8.dp))
                            Text(
                                text = activeTarget,
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
                            trackColor = Color(0xFF331B22)
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
                            trackColor = Color(0xFF132D38)
                        )
                    }

                    // SoE (Scroll of Enrage) Quantity (for taunters / party members)
                    if (config.isTaunter) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clip(RoundedCornerShape(6.dp))
                                .background(Color(0xFF161928))
                                .padding(horizontal = 8.dp, vertical = 5.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                Box(
                                    modifier = Modifier
                                        .size(6.dp)
                                        .clip(CircleShape)
                                        .background(if (telemetry.soeQty < 50) ErrorRed else SunGold)
                                )
                                Text(
                                    text = "Scroll of Enrage (SoE)",
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Medium,
                                    color = TextSecondary
                                )
                            }
                            Text(
                                text = "${telemetry.soeQty} pcs",
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold,
                                color = if (telemetry.soeQty < 50) ErrorRed else SunGold
                            )
                        }
                    }
                }
            }

            // Input Fields
            if (telemetry.running.not()) {
                OutlinedTextField(
                    value = config.username,
                    onValueChange = { onConfigChange(config.copy(username = it)) },
                    label = { Text("Username") },
                    singleLine = true,
                    enabled = !isPartyRunning,
                    modifier = Modifier.fillMaxWidth(),
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
                    label = { Text("Password") },
                    singleLine = true,
                    enabled = !isPartyRunning,
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
                        focusedBorderColor = accentColor,
                        unfocusedBorderColor = Color(0xFF334155),
                        focusedTextColor = TextPrimary,
                        unfocusedTextColor = TextPrimary
                    )
                )

                // Class Picker Dropdown
                ClassDropdown(
                    selectedClass = config.charClass,
                    enabled = !isPartyRunning,
                    onClassSelected = { onConfigChange(config.copy(charClass = it)) }
                )

                // Default Target Monsters Input
                OutlinedTextField(
                    value = config.defaultTarget,
                    onValueChange = { onConfigChange(config.copy(defaultTarget = it)) },
                    label = { Text("Default Target Monsters") },
                    placeholder = {
                        Text(
                            "e.g. Ascended Solstice,Blessless Deer",
                            color = TextMuted
                        )
                    },
                    singleLine = true,
                    enabled = !isPartyRunning,
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = accentColor,
                        unfocusedBorderColor = Color(0xFF334155),
                        focusedTextColor = TextPrimary,
                        unfocusedTextColor = TextPrimary
                    )
                )

                // Taunter Toggle Switch
                if (showTauntToggle) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text(
                                text = "Taunt Role",
                                fontSize = 13.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = TextPrimary
                            )
                            Text(
                                text = "Casts scroll/taunt on boss",
                                fontSize = 11.sp,
                                color = TextMuted
                            )
                        }
                        Switch(
                            checked = config.isTaunter,
                            onCheckedChange = { onConfigChange(config.copy(isTaunter = it)) },
                            enabled = !isPartyRunning,
                            colors = SwitchDefaults.colors(
                                checkedThumbColor = Color.White,
                                checkedTrackColor = accentColor,
                                uncheckedThumbColor = Color.LightGray,
                                uncheckedTrackColor = Color(0xFF334155)
                            )
                        )
                    }
                }

                // Eclipse Taunt Role Toggles (Moon Haze & Sunset Knight)
                if (showEclipseTauntToggles) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = "Moon Haze Taunter",
                                fontSize = 13.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = TextPrimary
                            )
                            Text(
                                text = "Taunts when Moonlight Gaze aura occurs",
                                fontSize = 11.sp,
                                color = TextMuted
                            )
                        }
                        Switch(
                            checked = config.moonHazeTaunter,
                            onCheckedChange = { onConfigChange(config.copy(moonHazeTaunter = it)) },
                            enabled = !isPartyRunning,
                            colors = SwitchDefaults.colors(
                                checkedThumbColor = Color.White,
                                checkedTrackColor = accentColor,
                                uncheckedThumbColor = Color.LightGray,
                                uncheckedTrackColor = Color(0xFF334155)
                            )
                        )
                    }

                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = "Sunset Knight Taunter",
                                fontSize = 13.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = TextPrimary
                            )
                            Text(
                                text = "Taunts when Sun's Warmth aura occurs",
                                fontSize = 11.sp,
                                color = TextMuted
                            )
                        }
                        Switch(
                            checked = config.sunsetKnightTaunter,
                            onCheckedChange = { onConfigChange(config.copy(sunsetKnightTaunter = it)) },
                            enabled = !isPartyRunning,
                            colors = SwitchDefaults.colors(
                                checkedThumbColor = Color.White,
                                checkedTrackColor = accentColor,
                                uncheckedThumbColor = Color.LightGray,
                                uncheckedTrackColor = Color(0xFF334155)
                            )
                        )
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ClassDropdown(
    selectedClass: String,
    enabled: Boolean,
    onClassSelected: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    var expanded by remember { mutableStateOf(false) }

    val filteredOptions = remember(selectedClass) {
        if (selectedClass.isBlank()) {
            AQW_CLASS_OPTIONS
        } else {
            val matches = AQW_CLASS_OPTIONS.filter { it.contains(selectedClass, ignoreCase = true) }
            matches.ifEmpty { AQW_CLASS_OPTIONS }
        }
    }

    ExposedDropdownMenuBox(
        expanded = expanded && enabled,
        onExpandedChange = { if (enabled) expanded = it },
        modifier = modifier.fillMaxWidth()
    ) {
        OutlinedTextField(
            value = selectedClass,
            onValueChange = {
                onClassSelected(it)
                expanded = true
            },
            singleLine = true,
            label = { Text("Character Class") },
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
            enabled = enabled,
            modifier = Modifier
                .menuAnchor(MenuAnchorType.PrimaryEditable, enabled)
                .fillMaxWidth(),
            colors = OutlinedTextFieldDefaults.colors(
                focusedBorderColor = PrimaryPurple,
                unfocusedBorderColor = Color(0xFF334155),
                focusedTextColor = TextPrimary,
                unfocusedTextColor = TextPrimary
            )
        )

        if (filteredOptions.isNotEmpty()) {
            ExposedDropdownMenu(
                expanded = expanded && enabled,
                onDismissRequest = { expanded = false },
                modifier = Modifier.background(CardDark)
            ) {
                filteredOptions.forEach { className ->
                    DropdownMenuItem(
                        text = { Text(text = className, color = TextPrimary) },
                        onClick = {
                            onClassSelected(className)
                            expanded = false
                        }
                    )
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ServerDropdown(
    selectedServer: String,
    enabled: Boolean,
    onServerSelected: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    var expanded by remember { mutableStateOf(false) }

    ExposedDropdownMenuBox(
        expanded = expanded && enabled,
        onExpandedChange = { if (enabled) expanded = !expanded },
        modifier = modifier
    ) {
        OutlinedTextField(
            value = selectedServer,
            onValueChange = {},
            readOnly = true,
            label = { Text("Server") },
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
            enabled = enabled,
            modifier = Modifier
                .menuAnchor(MenuAnchorType.PrimaryEditable, enabled),
            colors = OutlinedTextFieldDefaults.colors(
                focusedBorderColor = PrimaryPurple,
                unfocusedBorderColor = Color(0xFF334155),
                focusedTextColor = TextPrimary,
                unfocusedTextColor = TextPrimary
            )
        )

        ExposedDropdownMenu(
            expanded = expanded && enabled,
            onDismissRequest = { expanded = false },
            modifier = Modifier.background(CardDark)
        ) {
            SERVER_OPTIONS.forEach { serverName ->
                DropdownMenuItem(
                    text = { Text(text = serverName, color = TextPrimary) },
                    onClick = {
                        onServerSelected(serverName)
                        expanded = false
                    }
                )
            }
        }
    }
}

@Composable
fun MonsterTelemetryCard(
    modifier: Modifier = Modifier,
    monsters: List<MonsterTelemetry>,
    currentCell: String = ""
) {
    if (monsters.isEmpty()) return

    Card(
        modifier = modifier
            .fillMaxWidth()
            .border(1.dp, Color(0xFF3B1E28), RoundedCornerShape(14.dp)),
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF14101A))
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .size(8.dp)
                            .clip(CircleShape)
                            .background(Color(0xFFFF5252))
                    )
                    Text(
                        text = if (currentCell.isNotEmpty()) "MONSTERS (${currentCell.uppercase()})" else "CURRENT CELL MONSTERS",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFFFF7B72),
                        fontFamily = FontFamily.Monospace
                    )
                }

                val aliveCount = monsters.count { it.isAlive && it.hp > 0 }
                Text(
                    text = "$aliveCount / ${monsters.size} ALIVE",
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    color = if (aliveCount > 0) Color(0xFFFF5252) else TextMuted
                )
            }

            monsters.forEach { mon ->
                Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(6.dp)
                        ) {
                            Box(
                                modifier = Modifier
                                    .size(6.dp)
                                    .clip(CircleShape)
                                    .background(
                                        if (mon.isAlive && mon.hp > 0) Color(0xFFFF5252) else Color(
                                            0xFF64748B
                                        )
                                    )
                            )
                            Text(
                                text = mon.monName,
                                fontSize = 11.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = if (mon.isAlive && mon.hp > 0) TextPrimary else TextMuted
                            )
                        }
                        Text(
                            text = if (mon.hp > 0) "${mon.hp} / ${mon.maxHp} (${mon.hpPercent}%)" else "DEAD",
                            fontSize = 10.sp,
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.Medium,
                            color = if (mon.isAlive && mon.hp > 0) Color(0xFFFF7B72) else TextMuted
                        )
                    }
                    LinearProgressIndicator(
                        progress = { mon.hpFraction },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(5.dp)
                            .clip(RoundedCornerShape(3.dp)),
                        color = Color(0xFFFF5252),
                        trackColor = Color(0xFF2E171B)
                    )
                }
            }
        }
    }
}

@Composable
fun BotSessionStatsBar(
    modifier: Modifier = Modifier,
    stats: PartyStats,
    isRunning: Boolean,
    botType: String,
    accentColor: Color = PrimaryPurple
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .border(
                1.dp,
                if (isRunning) accentColor.copy(alpha = 0.35f) else Color(0xFF2E3350),
                RoundedCornerShape(12.dp)
            ),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF131522))
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 14.dp, vertical = 10.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Mode Title with status indicator
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Box(
                    modifier = Modifier
                        .size(8.dp)
                        .clip(CircleShape)
                        .background(if (isRunning) SuccessGreen else Color(0xFF64748B))
                )
                Text(
                    text = botType,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold,
                    color = accentColor
                )
            }

            // Stats items: Time Running & Cleared Loops
            Row(
                horizontalArrangement = Arrangement.spacedBy(16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Time Running
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    Icon(
                        imageVector = Icons.Filled.Timer,
                        contentDescription = "Time Running",
                        tint = TextSecondary,
                        modifier = Modifier.size(15.dp)
                    )
                    Text(
                        text = if (isRunning) stats.formattedTime else "00:00",
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.SemiBold,
                        color = if (isRunning) TextPrimary else TextMuted
                    )
                }

                // Total Cleared Loops
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    Icon(
                        imageVector = Icons.Filled.CheckCircle,
                        contentDescription = "Cleared Count",
                        tint = SuccessGreen,
                        modifier = Modifier.size(15.dp)
                    )
                    Text(
                        text = "${stats.clearedCount} Clears",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        color = SuccessGreen
                    )
                }
            }
        }
    }
}

@Composable
fun BackgroundOptimizationCard(
    isBatteryOptimizationIgnored: Boolean,
    hasNotificationPermission: Boolean,
    onRequestDisableBatteryOptimization: () -> Unit,
    onRequestNotificationPermission: () -> Unit,
    modifier: Modifier = Modifier
) {
    val allOptimal = isBatteryOptimizationIgnored && hasNotificationPermission
    var isExpanded by remember { mutableStateOf(!allOptimal) }
    val arrowRotation by animateFloatAsState(
        targetValue = if (isExpanded) 180f else 0f,
        label = "bgOptArrowRotation"
    )

    Card(
        modifier = modifier
            .fillMaxWidth()
            .border(
                1.dp,
                if (allOptimal) SuccessGreen.copy(alpha = 0.3f) else Color(0xFFF59E0B).copy(alpha = 0.4f),
                RoundedCornerShape(16.dp)
            ),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = if (allOptimal) Color(0xFF0F172A) else Color(0xFF1E1711)
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            // Header Row (tappable to expand / collapse)
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(8.dp))
                    .clickable { isExpanded = !isExpanded },
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(
                    modifier = Modifier.weight(1f),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Icon(
                        imageVector = if (allOptimal) Icons.Filled.CheckCircle else Icons.Filled.BatteryAlert,
                        contentDescription = "Background Settings",
                        tint = if (allOptimal) SuccessGreen else Color(0xFFF59E0B),
                        modifier = Modifier.size(20.dp)
                    )
                    Text(
                        text = "Background & Battery Settings",
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold,
                        color = TextPrimary
                    )
                }

                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    if (allOptimal) {
                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(6.dp))
                                .background(SuccessGreen.copy(alpha = 0.15f))
                                .padding(horizontal = 8.dp, vertical = 3.dp)
                        ) {
                            Text(
                                text = "OPTIMIZED",
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                color = SuccessGreen
                            )
                        }
                    } else {
                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(6.dp))
                                .background(Color(0xFFF59E0B).copy(alpha = 0.15f))
                                .padding(horizontal = 8.dp, vertical = 3.dp)
                        ) {
                            Text(
                                text = "SETUP NEEDED",
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color(0xFFF59E0B)
                            )
                        }
                    }

                    Icon(
                        imageVector = Icons.Filled.KeyboardArrowDown,
                        contentDescription = if (isExpanded) "Collapse" else "Expand",
                        tint = TextSecondary,
                        modifier = Modifier
                            .size(20.dp)
                            .rotate(arrowRotation)
                    )
                }
            }

            // Expandable details & actions
            AnimatedVisibility(
                visible = isExpanded,
                enter = expandVertically() + fadeIn(),
                exit = shrinkVertically() + fadeOut()
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 12.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Text(
                        text = if (allOptimal) {
                            "Background execution is fully enabled. The bot will keep running in the background and show live notifications when the app is minimized."
                        } else {
                            "To prevent Android from killing the bot when the app is minimized, please disable battery optimization and enable notifications."
                        },
                        fontSize = 12.sp,
                        color = TextSecondary,
                        lineHeight = 16.sp
                    )

                    // Battery Optimization Row
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(10.dp))
                            .background(Color(0xFF0B0D14))
                            .padding(horizontal = 12.dp, vertical = 10.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = "Battery Optimization",
                                fontSize = 12.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = TextPrimary
                            )
                            Text(
                                text = if (isBatteryOptimizationIgnored) "Disabled (Unrestricted background)" else "Active (May pause in background)",
                                fontSize = 11.sp,
                                color = if (isBatteryOptimizationIgnored) SuccessGreen else Color(
                                    0xFFF59E0B
                                )
                            )
                        }

                        if (!isBatteryOptimizationIgnored) {
                            Button(
                                onClick = onRequestDisableBatteryOptimization,
                                shape = RoundedCornerShape(8.dp),
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = Color(
                                        0xFFD97706
                                    )
                                ),
                                contentPadding = PaddingValues(horizontal = 12.dp, vertical = 6.dp)
                            ) {
                                Text(
                                    text = "Disable",
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = Color.White
                                )
                            }
                        }
                    }

                    // Notification Permission Row (if not granted)
                    if (!hasNotificationPermission) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clip(RoundedCornerShape(10.dp))
                                .background(Color(0xFF0B0D14))
                                .padding(horizontal = 12.dp, vertical = 10.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    text = "Background Notifications",
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.SemiBold,
                                    color = TextPrimary
                                )
                                Text(
                                    text = "Required for status updates when minimized",
                                    fontSize = 11.sp,
                                    color = Color(0xFFF59E0B)
                                )
                            }

                            Button(
                                onClick = onRequestNotificationPermission,
                                shape = RoundedCornerShape(8.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = PrimaryPurple),
                                contentPadding = PaddingValues(horizontal = 12.dp, vertical = 6.dp)
                            ) {
                                Text(
                                    text = "Enable",
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = Color.White
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun LiveLogConsole(
    modifier: Modifier = Modifier,
    logs: List<LogEntry>,
    onClearLogs: () -> Unit,
    title: String = "Live Console Logs"
) {
    val listState = rememberLazyListState()

    LaunchedEffect(logs.size) {
        if (logs.isNotEmpty()) {
            listState.animateScrollToItem(logs.size - 1)
        }
    }

    Card(
        modifier = modifier
            .fillMaxWidth()
            .height(300.dp)
            .border(1.dp, Color(0xFF2E3350), RoundedCornerShape(16.dp)),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF090A10))
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .fillMaxHeight()
                .padding(12.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = title,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    color = TextSecondary
                )
                IconButton(onClick = onClearLogs, modifier = Modifier.size(24.dp)) {
                    Icon(
                        imageVector = Icons.Filled.Delete,
                        contentDescription = "Clear Logs",
                        tint = TextMuted,
                        modifier = Modifier.size(16.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(6.dp))

            if (logs.isEmpty()) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "No logs yet. Logs will stream in real-time here.",
                        fontSize = 11.sp,
                        color = TextMuted
                    )
                }
            } else {
                LazyColumn(
                    state = listState,
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f),
                    verticalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    items(logs, key = { it.id }) { log ->
                        val cleanMessage =
                            froztt13.python.aqw.helper.BotHelper.stripAnsi(log.message)
                        val lower = cleanMessage.lowercase()
                        val textColor = when {
                            "error" in lower || "exception" in lower || "dead" in lower || "failed" in lower -> ErrorRed
                            "cleared" in lower || "success" in lower || "connected to" in lower -> SuccessGreen
                            "taunt" in lower || "soe" in lower || "warning" in lower -> SunGold
                            "login" in lower || "connecting" in lower || "joined" in lower -> MoonCyan
                            else -> TextSecondary
                        }
                        SelectionContainer {
                            Text(
                                text = "[${log.username}] $cleanMessage",
                                fontSize = 11.sp,
                                fontFamily = FontFamily.Monospace,
                                color = textColor
                            )
                        }
                    }
                }
            }
        }
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF0B0D14)
@Composable
private fun SlotCardIdlePreview() {
    MyApplicationTheme {
        SlotCard(
            slotKey = "slot1",
            title = "Slot 1 (Lord of Order / Lead)",
            config = SlotConfig(
                username = "LordLead",
                charClass = "Lord of Order",
                role = "master",
                isTaunter = true,
                defaultTarget = "Ascended Solstice,Blessless Deer"
            ),
            telemetry = SlotTelemetry(running = false),
            isPartyRunning = false,
            accentColor = PrimaryPurple,
            onConfigChange = {}
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF0B0D14)
@Composable
private fun SlotCardActivePreview() {
    MyApplicationTheme {
        SlotCard(
            slotKey = "slot1",
            title = "Slot 1 (Lord of Order / Lead)",
            config = SlotConfig(
                username = "LordLead",
                charClass = "Lord of Order",
                role = "master",
                isTaunter = true,
                defaultTarget = "Ascended Solstice,Blessless Deer"
            ),
            telemetry = SlotTelemetry(
                running = true,
                isConnected = true,
                map = "ascendeclipse",
                cell = "r3",
                pad = "Left",
                hp = 4200,
                maxHp = 5000,
                mp = 80,
                maxMp = 100,
                soeQty = 150,
                targetMonsters = "Ascended Solstice"
            ),
            isPartyRunning = true,
            accentColor = PrimaryPurple,
            onConfigChange = {}
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF0B0D14)
@Composable
private fun MonsterTelemetryCardPreview() {
    MyApplicationTheme {
        MonsterTelemetryCard(
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
            ),
            currentCell = "r3"
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF0B0D14)
@Composable
private fun LiveLogConsolePreview() {
    MyApplicationTheme {
        LiveLogConsole(
            logs = listOf(
                LogEntry(
                    botType = "temple",
                    username = "LordLead",
                    message = "Connected to room 9099"
                ),
                LogEntry(
                    botType = "temple",
                    username = "LordLead",
                    message = "Taunting boss: Success!"
                ),
                LogEntry(
                    botType = "temple",
                    username = "LordLead",
                    message = "Error: target not found (recovered)"
                )
            ),
            onClearLogs = {}
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF0B0D14)
@Composable
private fun BotSessionStatsBarPreview() {
    MyApplicationTheme {
        BotSessionStatsBar(
            stats = PartyStats(timeRunning = 3725L, clearedCount = 12),
            isRunning = true,
            botType = "MidnightSunBot",
            accentColor = SunGold
        )
    }
}

