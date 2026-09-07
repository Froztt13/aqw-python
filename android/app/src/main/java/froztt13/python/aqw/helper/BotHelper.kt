package froztt13.python.aqw.helper

import android.util.Log
import com.chaquo.python.PyObject
import com.chaquo.python.Python
import froztt13.python.aqw.data.DoomAccount
import froztt13.python.aqw.data.DoomAccountTelemetry
import froztt13.python.aqw.data.EclipseConfig
import froztt13.python.aqw.data.LogEntry
import froztt13.python.aqw.data.MonsterTelemetry
import froztt13.python.aqw.data.PartyStats
import froztt13.python.aqw.data.SlotConfig
import froztt13.python.aqw.data.SlotTelemetry
import froztt13.python.aqw.data.TempleConfig
import froztt13.python.aqw.data.WeeklyDoomConfig
import froztt13.python.aqw.data.WeeklyDoomTelemetry
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.CopyOnWriteArrayList

object BotHelper {
    private const val TAG = "BotHelper"
    private var pyBridge: PyObject? = null
    private var isBridgeInitialized = false

    private val logListeners = CopyOnWriteArrayList<(LogEntry) -> Unit>()

    @Synchronized
    fun getBridge(): PyObject? {
        if (pyBridge == null) {
            try {
                if (Python.isStarted()) {
                    val py = Python.getInstance()
                    pyBridge = py.getModule("mobile_bridge")
                    ensureBridgeInitialized()
                }
            } catch (e: Exception) {
                Log.e(TAG, "Failed to get Python bridge: ${e.message}", e)
            }
        }
        return pyBridge
    }

    private fun ensureBridgeInitialized() {
        if (!isBridgeInitialized) {
            try {
                val bridge = pyBridge ?: return
                val callback: (String, String, String) -> Unit = { botType, username, msg ->
                    dispatchLog(botType, username, msg)
                }
                bridge.callAttr("init_bridge", callback)
                isBridgeInitialized = true
            } catch (e: Exception) {
                Log.e(TAG, "Bridge init_bridge failed: ${e.message}", e)
            }
        }
    }

    private val ANSI_REGEX =
        Regex("""(?:\u001B|\x1B)\[[0-9;]*[a-zA-Z]|\[\d{1,3}(?:;\d{1,3})*m|(?:\u001B|\x1B)[@-_]""")

    fun stripAnsi(text: String): String {
        return text.replace(ANSI_REGEX, "").trim()
    }

    private fun dispatchLog(botType: String, username: String, message: String) {
        val cleanMsg = stripAnsi(message)
        if (cleanMsg.isEmpty()) return
        val entry = LogEntry(botType = botType, username = username, message = cleanMsg)
        for (listener in logListeners) {
            try {
                listener(entry)
            } catch (e: Exception) {
                Log.e(TAG, "Error in log listener: ${e.message}")
            }
        }
    }

    fun registerLogListener(filterBotType: String? = null, onLog: (LogEntry) -> Unit): () -> Unit {
        val listener: (LogEntry) -> Unit = { entry ->
            if (filterBotType == null ||
                entry.botType.equals(filterBotType, ignoreCase = true) ||
                entry.botType.equals("System", ignoreCase = true)
            ) {
                onLog(entry)
            }
        }
        logListeners.add(listener)
        // Ensure bridge is initialized so logs can be captured
        getBridge()
        return {
            logListeners.remove(listener)
        }
    }

    // --- Bridge Operations ---
    suspend fun startParty(methodName: String, configJson: String): Pair<Boolean, String?> =
        withContext(Dispatchers.IO) {
            try {
                val bridge =
                    getBridge() ?: return@withContext Pair(false, "Python Bridge not ready")
                val resJsonStr = bridge.callAttr(methodName, configJson)?.toString() ?: "{}"
                val resObj = JSONObject(resJsonStr)
                val success = resObj.optBoolean("success", false)
                val error = if (resObj.has("error")) resObj.optString("error") else null
                Pair(success, error)
            } catch (e: Exception) {
                Log.e(TAG, "startParty error ($methodName): ${e.message}", e)
                Pair(false, e.message)
            }
        }

    suspend fun stopParty(methodName: String): Boolean = withContext(Dispatchers.IO) {
        try {
            val bridge = getBridge() ?: return@withContext false
            bridge.callAttr(methodName)
            true
        } catch (e: Exception) {
            Log.e(TAG, "stopParty error ($methodName): ${e.message}", e)
            false
        }
    }

    suspend fun loadConfig(methodName: String): String? = withContext(Dispatchers.IO) {
        try {
            val bridge = getBridge() ?: return@withContext null
            bridge.callAttr(methodName)?.toString()
        } catch (e: Exception) {
            Log.e(TAG, "loadConfig error ($methodName): ${e.message}", e)
            null
        }
    }

    suspend fun resetConfig(methodName: String): String? = withContext(Dispatchers.IO) {
        try {
            val bridge = getBridge() ?: return@withContext null
            bridge.callAttr(methodName)?.toString()
        } catch (e: Exception) {
            Log.e(TAG, "resetConfig error ($methodName): ${e.message}", e)
            null
        }
    }

    suspend fun saveConfig(methodName: String, configJson: String): Boolean =
        withContext(Dispatchers.IO) {
            try {
                val bridge = getBridge() ?: return@withContext false
                bridge.callAttr(methodName, configJson)
                true
            } catch (e: Exception) {
                Log.e(TAG, "saveConfig error ($methodName): ${e.message}", e)
                false
            }
        }

    suspend fun getStatus(methodName: String): String? = withContext(Dispatchers.IO) {
        try {
            val bridge = getBridge() ?: return@withContext null
            bridge.callAttr(methodName)?.toString()
        } catch (e: Exception) {
            Log.w(TAG, "getStatus error ($methodName): ${e.message}")
            null
        }
    }

    // --- Parsing and Serialization ---
    fun parseSlotTelemetryMap(jsonStr: String): Map<String, SlotTelemetry> {
        val result = mutableMapOf<String, SlotTelemetry>()
        try {
            val obj = JSONObject(jsonStr)
            for (key in listOf("slot1", "slot2", "slot3", "slot4")) {
                val sObj = obj.optJSONObject(key) ?: continue
                val running = sObj.optBoolean("running", false)
                if (running) {
                    val monstersList = mutableListOf<MonsterTelemetry>()
                    val monstersArr = sObj.optJSONArray("monsters")
                    if (monstersArr != null) {
                        for (i in 0 until monstersArr.length()) {
                            val mObj = monstersArr.optJSONObject(i) ?: continue
                            monstersList.add(
                                MonsterTelemetry(
                                    monMapId = mObj.optString("id", ""),
                                    monName = mObj.optString("name", ""),
                                    hp = mObj.optInt("hp", 0),
                                    maxHp = mObj.optInt("max_hp", 0),
                                    isAlive = mObj.optBoolean("is_alive", false)
                                )
                            )
                        }
                    }

                    val cooldownsMap = mutableMapOf<Int, Double>()
                    val cooldownsObj = sObj.optJSONObject("cooldowns")
                    if (cooldownsObj != null) {
                        val keys = cooldownsObj.keys()
                        while (keys.hasNext()) {
                            val kStr = keys.next()
                            val kInt = kStr.toIntOrNull()
                            if (kInt != null) {
                                cooldownsMap[kInt] = cooldownsObj.optDouble(kStr, 0.0)
                            }
                        }
                    }

                    result[key] = SlotTelemetry(
                        running = true,
                        isConnected = sObj.optBoolean("is_connected", false),
                        map = sObj.optString("map", "-"),
                        cell = sObj.optString("cell", "-"),
                        pad = sObj.optString("pad", "-"),
                        hp = sObj.optInt("hp", 0),
                        maxHp = sObj.optInt("max_hp", 0),
                        mp = sObj.optInt("mp", 0),
                        maxMp = sObj.optInt("max_mp", 0),
                        isDead = sObj.optBoolean("is_dead", false),
                        cooldowns = cooldownsMap,
                        tauntError = sObj.optBoolean("taunt_error", false),
                        soeQty = sObj.optInt("soe_qty", 0),
                        monsters = monstersList,
                        targetMonsters = sObj.optString("target_monsters", "")
                    )
                } else {
                    result[key] = SlotTelemetry(running = false)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "parseSlotTelemetryMap error: ${e.message}")
        }
        return result
    }

    fun parsePartyStats(jsonStr: String): PartyStats {
        try {
            val obj = JSONObject(jsonStr)
            val statsObj = obj.optJSONObject("_stats")
            if (statsObj != null) {
                return PartyStats(
                    timeRunning = statsObj.optLong("time_running", 0L),
                    clearedCount = statsObj.optInt("cleared_count", 0)
                )
            }
        } catch (e: Exception) {
            Log.e(TAG, "parsePartyStats error: ${e.message}")
        }
        return PartyStats()
    }

    fun parsePartyError(jsonStr: String): String? {
        try {
            val obj = JSONObject(jsonStr)
            if (obj.has("_error") && !obj.isNull("_error")) {
                val err = obj.optString("_error", "")
                if (err.isNotEmpty()) return err
            }
        } catch (e: Exception) {
            Log.e(TAG, "parsePartyError error: ${e.message}")
        }
        return null
    }

    fun parseTempleConfig(jsonStr: String): TempleConfig {
        val obj = JSONObject(jsonStr)
        val server = obj.optString("server", "Alteon")
        val room = obj.optInt("room_number", 9099)
        val botType = obj.optString("temple_bot_type", "MidnightSunBot")
        val slotsObj = obj.optJSONObject("slots") ?: JSONObject()

        val slots = mutableMapOf<String, SlotConfig>()
        val defaultClasses = mapOf(
            "slot1" to "ArchPaladin",
            "slot2" to "StoneCrusher",
            "slot3" to "Legion Revenant",
            "slot4" to "Lord of Order"
        )
        val defaultTargets = mapOf(
            "slot1" to "Ascended Midnight,Blessless Deer",
            "slot2" to "Ascended Midnight,Blessless Deer",
            "slot3" to "Ascended Midnight,Blessless Deer",
            "slot4" to "Ascended Midnight,Blessless Deer"
        )
        for (key in listOf("slot1", "slot2", "slot3", "slot4")) {
            val sObj = slotsObj.optJSONObject(key) ?: JSONObject()
            slots[key] = SlotConfig(
                username = sObj.optString("username", ""),
                password = sObj.optString("password", ""),
                charClass = sObj.optString("char_class", defaultClasses[key] ?: "ArchPaladin"),
                role = sObj.optString("role", if (key == "slot1") "master" else "slave"),
                isTaunter = sObj.optBoolean("is_taunter", key == "slot1"),
                moonHazeTaunter = sObj.optBoolean("moon_haze_taunter", false),
                sunsetKnightTaunter = sObj.optBoolean("sunset_knight_taunter", false),
                defaultTarget = sObj.optString("default_target", defaultTargets[key] ?: "")
            )
        }
        return TempleConfig(
            server = server,
            roomNumber = room,
            templeBotType = botType,
            slots = slots
        )
    }

    fun serializeTempleConfig(cfg: TempleConfig): String {
        val obj = JSONObject()
        obj.put("server", cfg.server)
        obj.put("room_number", cfg.roomNumber)
        obj.put("temple_bot_type", cfg.templeBotType)
        val slotsObj = JSONObject()
        for ((k, v) in cfg.slots) {
            val s = JSONObject()
            s.put("username", v.username)
            s.put("password", v.password)
            s.put("char_class", v.charClass)
            s.put("role", v.role)
            s.put("is_taunter", v.isTaunter)
            s.put("moon_haze_taunter", v.moonHazeTaunter)
            s.put("sunset_knight_taunter", v.sunsetKnightTaunter)
            s.put("default_target", v.defaultTarget)
            slotsObj.put(k, s)
        }
        obj.put("slots", slotsObj)
        return obj.toString()
    }

    fun parseEclipseConfig(jsonStr: String): EclipseConfig {
        val obj = JSONObject(jsonStr)
        val server = obj.optString("server", "Alteon")
        val room = obj.optInt("room_number", 9099)
        val slotsObj = obj.optJSONObject("slots") ?: JSONObject()

        val slots = mutableMapOf<String, SlotConfig>()
        val defaultClasses = mapOf(
            "slot1" to "Legion Revenant",
            "slot2" to "StoneCrusher",
            "slot3" to "ArchPaladin",
            "slot4" to "Lord of Order"
        )
        val defaultTargets = mapOf(
            "slot1" to "Ascended Solstice,Blessless Deer",
            "slot2" to "Ascended Solstice",
            "slot3" to "Ascended Midnight",
            "slot4" to "Ascended Midnight"
        )
        for (key in listOf("slot1", "slot2", "slot3", "slot4")) {
            val sObj = slotsObj.optJSONObject(key) ?: JSONObject()
            slots[key] = SlotConfig(
                username = sObj.optString("username", ""),
                password = sObj.optString("password", ""),
                charClass = sObj.optString("char_class", defaultClasses[key] ?: "Legion Revenant"),
                role = sObj.optString("role", if (key == "slot1") "master" else "slave"),
                isTaunter = sObj.optBoolean(
                    "is_taunter",
                    key == "slot1" || key == "slot3" || key == "slot4"
                ),
                moonHazeTaunter = sObj.optBoolean("moon_haze_taunter", key == "slot3"),
                sunsetKnightTaunter = sObj.optBoolean("sunset_knight_taunter", key == "slot4"),
                defaultTarget = sObj.optString("default_target", defaultTargets[key] ?: "")
            )
        }
        return EclipseConfig(server = server, roomNumber = room, slots = slots)
    }

    fun serializeEclipseConfig(cfg: EclipseConfig): String {
        val obj = JSONObject()
        obj.put("server", cfg.server)
        obj.put("room_number", cfg.roomNumber)
        val slotsObj = JSONObject()
        for ((k, v) in cfg.slots) {
            val s = JSONObject()
            s.put("username", v.username)
            s.put("password", v.password)
            s.put("char_class", v.charClass)
            s.put("role", v.role)
            s.put("is_taunter", v.isTaunter)
            s.put("moon_haze_taunter", v.moonHazeTaunter)
            s.put("sunset_knight_taunter", v.sunsetKnightTaunter)
            s.put("default_target", v.defaultTarget)
            slotsObj.put(k, s)
        }
        obj.put("slots", slotsObj)
        return obj.toString()
    }

    fun parseStringList(array: JSONArray?): List<String> {
        if (array == null) return emptyList()
        val list = mutableListOf<String>()
        for (i in 0 until array.length()) {
            list.add(array.optString(i))
        }
        return list
    }

    fun parseWeeklyDoomConfig(jsonStr: String): WeeklyDoomConfig {
        return try {
            val obj = JSONObject(jsonStr)
            val server = obj.optString("server", "Alteon")
            val accountsArr = obj.optJSONArray("accounts")
            val accounts = mutableListOf<DoomAccount>()
            if (accountsArr != null) {
                for (i in 0 until accountsArr.length()) {
                    val aObj = accountsArr.optJSONObject(i) ?: continue
                    accounts.add(
                        DoomAccount(
                            id = aObj.optString("id", java.util.UUID.randomUUID().toString()),
                            username = aObj.optString("username", ""),
                            password = aObj.optString("password", ""),
                            enabled = aObj.optBoolean("enabled", true)
                        )
                    )
                }
            }
            if (accounts.isEmpty()) {
                accounts.add(DoomAccount())
            }
            WeeklyDoomConfig(server = server, accounts = accounts)
        } catch (e: Exception) {
            Log.e(TAG, "parseWeeklyDoomConfig error: ${e.message}")
            WeeklyDoomConfig()
        }
    }

    fun serializeWeeklyDoomConfig(cfg: WeeklyDoomConfig): String {
        val obj = JSONObject()
        obj.put("server", cfg.server)
        val accountsArr = JSONArray()
        for (acc in cfg.accounts) {
            val aObj = JSONObject()
            aObj.put("id", acc.id)
            aObj.put("username", acc.username)
            aObj.put("password", acc.password)
            aObj.put("enabled", acc.enabled)
            accountsArr.put(aObj)
        }
        obj.put("accounts", accountsArr)
        return obj.toString()
    }

    fun parseWeeklyDoomTelemetry(jsonStr: String): WeeklyDoomTelemetry {
        return try {
            val obj = JSONObject(jsonStr)
            val running = obj.optBoolean("running", false)
            val currentIndex = obj.optInt("current_index", 0)
            val currentUsername = obj.optString("current_username", "")
            val totalAccounts = obj.optInt("total_accounts", 0)
            val completedAccounts = obj.optInt("completed_accounts", 0)
            val timeRunning = obj.optLong("time_running", 0L)

            val accountsMap = mutableMapOf<String, DoomAccountTelemetry>()
            val accObj = obj.optJSONObject("accounts")
            if (accObj != null) {
                val keys = accObj.keys()
                while (keys.hasNext()) {
                    val k = keys.next()
                    val a = accObj.optJSONObject(k) ?: continue
                    val dropsArr = a.optJSONArray("wheel_drops")
                    val dropsList = mutableListOf<String>()
                    if (dropsArr != null) {
                        for (i in 0 until dropsArr.length()) {
                            dropsList.add(dropsArr.optString(i))
                        }
                    }
                    accountsMap[k] = DoomAccountTelemetry(
                        id = a.optString("id", k),
                        username = a.optString("username", ""),
                        status = a.optString("status", "Idle"),
                        message = a.optString("message", ""),
                        hasEioda = a.optBoolean("has_eioda", false),
                        wheelDrops = dropsList
                    )
                }
            }

            WeeklyDoomTelemetry(
                running = running,
                currentIndex = currentIndex,
                currentUsername = currentUsername,
                totalAccounts = totalAccounts,
                completedAccounts = completedAccounts,
                timeRunning = timeRunning,
                accounts = accountsMap
            )
        } catch (e: Exception) {
            Log.e(TAG, "parseWeeklyDoomTelemetry error: ${e.message}")
            WeeklyDoomTelemetry()
        }
    }
}
