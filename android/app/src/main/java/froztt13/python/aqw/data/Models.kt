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

enum class ThresholdType {
    NONE, HP, MP
}

data class Skill(
    val id: String = java.util.UUID.randomUUID().toString(),
    val index: Int = 1,
    val thresholdType: ThresholdType = ThresholdType.NONE,
    val operator: String = "<",
    val thresholdValue: Int = 0
) {
    fun hasThreshold(): Boolean = thresholdType != ThresholdType.NONE && thresholdValue > 0

    fun thresholdSummary(): String {
        return if (hasThreshold()) {
            "${thresholdType.name} $operator $thresholdValue%"
        } else {
            "Always"
        }
    }
}

data class SlaveSlotConfig(
    val enabled: Boolean = true,
    val username: String = "",
    val password: String = "",
    val charClass: String = "Lord of Order",
    val skills: List<Skill> = listOf(
        Skill(index = 1),
        Skill(index = 2),
        Skill(index = 3),
        Skill(index = 4)
    ),
    val isTaunter: Boolean = false
)

data class SlaveryConfig(
    val server: String = "Gravelyn",
    val followPlayer: String = "",
    val defaultRoomNumber: Int = 9099,
    val copyWalk: Boolean = true,
    val autoZone: String = "none",
    val targetsPriority: String = "Defense Drone,Staff of Inversion",
    val whitelist: String = "Treasure Chest, Void Aura",
    val lockedZones: List<String> = listOf(
        "ultraezrajal",
        "ultrawarden",
        "ultraengineer",
        "doomvault",
        "doomvaultb",
        "championdrakath",
        "tercessuinotlim",
        "icestormunder"
    ),
    val slots: Map<String, SlaveSlotConfig> = mapOf(
        "slot1" to SlaveSlotConfig(enabled = true, charClass = "Lord of Order"),
        "slot2" to SlaveSlotConfig(enabled = true, charClass = "Legion Revenant"),
        "slot3" to SlaveSlotConfig(enabled = false, charClass = "ArchPaladin"),
        "slot4" to SlaveSlotConfig(enabled = false, charClass = "StoneCrusher")
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
    val eclipse: BotSummary = BotSummary(),
    val doom: BotSummary = BotSummary(),
    val slavery: BotSummary = BotSummary(),
    val general: BotSummary = BotSummary()
)

data class DoomAccount(
    val id: String = java.util.UUID.randomUUID().toString(),
    val username: String = "",
    val password: String = "",
    val enabled: Boolean = true
)

data class WeeklyDoomConfig(
    val server: String = "Alteon",
    val accounts: List<DoomAccount> = listOf(DoomAccount())
)

data class DoomAccountTelemetry(
    val id: String = "",
    val username: String = "",
    val status: String = "Idle",
    val message: String = "",
    val hasEioda: Boolean = false,
    val wheelDrops: List<String> = emptyList()
)

data class WeeklyDoomTelemetry(
    val running: Boolean = false,
    val currentIndex: Int = 0,
    val currentUsername: String = "",
    val totalAccounts: Int = 0,
    val completedAccounts: Int = 0,
    val timeRunning: Long = 0L,
    val accounts: Map<String, DoomAccountTelemetry> = emptyMap()
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

private val logIdCounter = java.util.concurrent.atomic.AtomicLong(1L)

data class LogEntry(
    val id: Long = logIdCounter.incrementAndGet(),
    val timestamp: Long = System.currentTimeMillis(),
    val botType: String,
    val username: String,
    val message: String
)

data class GeneralTaskInfo(
    val id: String = "",
    val name: String = "",
    val description: String = "",
    val defaultQty: Int = 1,
    val trackedItem: String = "",
    val questId: Int = 0
)

data class GeneralSubModuleInfo(
    val id: String = "",
    val name: String = "",
    val category: String = "",
    val description: String = "",
    val tasks: List<GeneralTaskInfo> = emptyList()
)

data class GeneralBotConfig(
    val server: String = "Alteon",
    val roomNumber: Int = 9099,
    val username: String = "",
    val password: String = "",
    val subModule: String = "lr",
    val task: String = "spellscroll",
    val targetQty: Int = 20,
    val soloClass: String = "Void Highlord",
    val farmClass: String = "Legion Revenant"
)

data class GeneralBotTelemetry(
    val running: Boolean = false,
    val isConnected: Boolean = false,
    val username: String = "",
    val subModule: String = "",
    val subModuleName: String = "",
    val task: String = "",
    val taskName: String = "",
    val trackedItem: String = "",
    val currentQty: Int = 0,
    val targetQty: Int = 0,
    val status: String = "Idle",
    val message: String = "",
    val map: String = "-",
    val cell: String = "-",
    val pad: String = "-",
    val hp: Int = 0,
    val maxHp: Int = 0,
    val mp: Int = 0,
    val maxMp: Int = 0,
    val isDead: Boolean = false,
    val cooldowns: Map<Int, Double> = emptyMap(),
    val timeRunning: Long = 0L
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

    val progressFraction: Float
        get() = if (targetQty > 0) (currentQty.toFloat() / targetQty.toFloat()).coerceIn(
            0f,
            1f
        ) else 0f

    val progressPercent: Int
        get() = (progressFraction * 100).toInt()
}
