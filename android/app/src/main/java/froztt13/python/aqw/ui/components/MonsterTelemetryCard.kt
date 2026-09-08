package froztt13.python.aqw.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import froztt13.python.aqw.data.MonsterTelemetry
import froztt13.python.aqw.ui.theme.MyApplicationTheme
import froztt13.python.aqw.ui.theme.TextMuted
import froztt13.python.aqw.ui.theme.TextPrimary

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
