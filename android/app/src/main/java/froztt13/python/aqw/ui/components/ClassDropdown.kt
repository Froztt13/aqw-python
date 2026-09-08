package froztt13.python.aqw.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.MenuAnchorType
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import froztt13.python.aqw.ui.theme.CardDark
import froztt13.python.aqw.ui.theme.PrimaryPurple
import froztt13.python.aqw.ui.theme.TextPrimary

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
