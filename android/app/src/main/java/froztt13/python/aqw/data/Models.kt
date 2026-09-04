package froztt13.python.aqw.data

data class SlotConfig(
    val username: String = "",
    val password: String = "",
    val charClass: String = "ArchPaladin",
    val role: String = "slave",
    val isTaunter: Boolean = false,
    val moonHazeTaunter: Boolean = false,
    val sunsetKnightTaunter: Boolean = false,
    val defaultTarget: String = ""
)

data class TempleConfig(
    val server: String = "Alteon",
    val roomNumber: Int = 9099,
    val templeBotType: String = "MidnightSunBot",
    val slots: Map<String, SlotConfig> = mapOf(
        "slot1" to SlotConfig(
            charClass = "ArchPaladin",
            role = "master",
            isTaunter = true,
            defaultTarget = "Ascended Midnight,Blessless Deer"
        ),
        "slot2" to SlotConfig(
            charClass = "StoneCrusher",
            role = "slave",
            isTaunter = false,
            defaultTarget = "Ascended Midnight,Blessless Deer"
        ),
        "slot3" to SlotConfig(
            charClass = "Legion Revenant",
            role = "slave",
            isTaunter = false,
            defaultTarget = "Ascended Midnight,Blessless Deer"
        ),
        "slot4" to SlotConfig(
            charClass = "Lord of Order",
            role = "slave",
            isTaunter = false,
            defaultTarget = "Ascended Midnight,Blessless Deer"
        )
    )
)

data class EclipseConfig(
    val server: String = "Alteon",
    val roomNumber: Int = 9099,
    val slots: Map<String, SlotConfig> = mapOf(
        "slot1" to SlotConfig(
            charClass = "Legion Revenant",
            role = "master",
            isTaunter = true,
            moonHazeTaunter = false,
            sunsetKnightTaunter = false,
            defaultTarget = "Ascended Solstice,Blessless Deer"
        ),
        "slot2" to SlotConfig(
            charClass = "StoneCrusher",
            role = "slave",
            isTaunter = false,
            moonHazeTaunter = false,
            sunsetKnightTaunter = false,
            defaultTarget = "Ascended Solstice"
        ),
        "slot3" to SlotConfig(
            charClass = "ArchPaladin",
            role = "slave",
            isTaunter = true,
            moonHazeTaunter = true,
            sunsetKnightTaunter = false,
            defaultTarget = "Ascended Midnight"
        ),
        "slot4" to SlotConfig(
            charClass = "Lord of Order",
            role = "slave",
            isTaunter = true,
            moonHazeTaunter = false,
            sunsetKnightTaunter = true,
            defaultTarget = "Ascended Midnight"
        )
    )
)

data class MonsterTelemetry(
    val monMapId: String = "",
    val monName: String = "",
    val hp: Int = 0,
    val maxHp: Int = 0,
    val isAlive: Boolean = false
) {
    val hpFraction: Float
        get() = if (maxHp > 0) (hp.toFloat() / maxHp.toFloat()).coerceIn(0f, 1f) else 0f
    val hpPercent: Int
        get() = if (maxHp > 0) ((hp.toDouble() / maxHp.toDouble()) * 100).toInt() else 0
}

data class SlotTelemetry(
    val running: Boolean = false,
    val isConnected: Boolean = false,
    val map: String = "-",
    val cell: String = "-",
    val pad: String = "-",
    val hp: Int = 0,
    val maxHp: Int = 0,
    val mp: Int = 0,
    val maxMp: Int = 0,
    val isDead: Boolean = false,
    val cooldowns: Map<Int, Double> = emptyMap(),
    val tauntError: Boolean = false,
    val soeQty: Int = 0,
    val monsters: List<MonsterTelemetry> = emptyList(),
    val targetMonsters: String = ""
)

data class PartyStats(
    val timeRunning: Long = 0L,
    val clearedCount: Int = 0
) {
    val formattedTime: String
        get() {
            val hours = timeRunning / 3600
            val minutes = (timeRunning % 3600) / 60
            val seconds = timeRunning % 60
            return if (hours > 0) {
                String.format(
                    java.util.Locale.getDefault(),
                    "%02d:%02d:%02d",
                    hours,
                    minutes,
                    seconds
                )
            } else {
                String.format(java.util.Locale.getDefault(), "%02d:%02d", minutes, seconds)
            }
        }
}

data class BotSummary(
    val running: Boolean = false,
    val count: Int = 0,
    val members: List<String> = emptyList(),
    val timeRunning: Long = 0L
)

data class HubOverview(
    val temple: BotSummary = BotSummary(),
    val eclipse: BotSummary = BotSummary()
)

private val logIdCounter = java.util.concurrent.atomic.AtomicLong(1L)

data class LogEntry(
    val id: Long = logIdCounter.incrementAndGet(),
    val timestamp: Long = System.currentTimeMillis(),
    val botType: String,
    val username: String,
    val message: String
)
