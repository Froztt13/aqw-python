package froztt13.python.aqw.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import froztt13.python.aqw.ui.theme.BgDark
import froztt13.python.aqw.ui.theme.DoomCrimson
import froztt13.python.aqw.ui.theme.MyApplicationTheme
import froztt13.python.aqw.ui.theme.SuccessGreen
import froztt13.python.aqw.ui.theme.TextPrimary
import froztt13.python.aqw.ui.theme.TextSecondary

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DefaultTopBar(
    title: String,
    modifier: Modifier = Modifier,
    onBack: (() -> Unit)? = null,
    statusDotColor: Color? = null,
    containerColor: Color = BgDark,
    titleContent: (@Composable () -> Unit)? = null,
    actions: @Composable RowScope.() -> Unit = {}
) {
    TopAppBar(
        modifier = modifier,
        title = {
            if (titleContent != null) {
                titleContent()
            } else {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    if (statusDotColor != null) {
                        Box(
                            modifier = Modifier
                                .size(10.dp)
                                .clip(CircleShape)
                                .background(statusDotColor)
                        )
                    }
                    Text(
                        text = title,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = TextPrimary
                    )
                }
            }
        },
        navigationIcon = {
            if (onBack != null) {
                IconButton(onClick = onBack) {
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                        contentDescription = "Back",
                        tint = TextPrimary
                    )
                }
            }
        },
        actions = actions,
        colors = TopAppBarDefaults.topAppBarColors(containerColor = containerColor)
    )
}

/**
 * Convenience toggle action button for screens that feature a settings drawer/panel.
 */
@Composable
fun TopBarSettingsButton(
    active: Boolean,
    onClick: () -> Unit,
    tintColor: Color = DoomCrimson,
    modifier: Modifier = Modifier
) {
    IconButton(
        onClick = onClick,
        modifier = modifier
            .clip(CircleShape)
            .background(if (active) tintColor.copy(alpha = 0.2f) else Color.Transparent)
    ) {
        Icon(
            imageVector = Icons.Filled.Settings,
            contentDescription = "Toggle Settings",
            tint = if (active) tintColor else TextSecondary
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF0B0D14)
@Composable
private fun DefaultTopBarPreview() {
    MyApplicationTheme {
        DefaultTopBar(
            title = "WEEKLY DOOM BOT",
            statusDotColor = SuccessGreen,
            onBack = {},
            actions = {
                TopBarSettingsButton(
                    active = true,
                    onClick = {},
                    tintColor = DoomCrimson
                )
            }
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF0B0D14)
@Composable
private fun DefaultTopBarIdlePreview() {
    MyApplicationTheme {
        DefaultTopBar(
            title = "WEEKLY DOOM BOT",
            statusDotColor = DoomCrimson,
            onBack = {},
            actions = {
                TopBarSettingsButton(
                    active = false,
                    onClick = {},
                    tintColor = DoomCrimson
                )
            }
        )
    }
}
