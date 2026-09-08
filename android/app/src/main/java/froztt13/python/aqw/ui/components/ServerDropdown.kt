package froztt13.python.aqw.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.MenuAnchorType
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
fun ServerDropdown(
    selectedServer: String,
    enabled: Boolean,
    onServerSelected: (String) -> Unit,
    modifier: Modifier = Modifier,
    contentPadding: PaddingValues = OutlinedTextFieldDefaults.contentPadding()
) {
    var expanded by remember { mutableStateOf(false) }

    ExposedDropdownMenuBox(
        expanded = expanded && enabled,
        onExpandedChange = { if (enabled) expanded = !expanded },
        modifier = modifier
    ) {
        CustomOutlinedTextField(
            value = selectedServer,
            onValueChange = {},
            readOnly = true,
            label = { Text("Server") },
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
            enabled = enabled,
            modifier = Modifier
                .menuAnchor(MenuAnchorType.PrimaryEditable, enabled),
            contentPadding = contentPadding,
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
