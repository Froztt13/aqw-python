package froztt13.python.aqw.viewmodel

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import froztt13.python.aqw.data.LogEntry
import froztt13.python.aqw.data.PartyStats
import froztt13.python.aqw.data.SlotConfig
import froztt13.python.aqw.data.SlotTelemetry
import froztt13.python.aqw.data.TempleConfig
import froztt13.python.aqw.helper.BotHelper
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlin.time.Duration.Companion.milliseconds

class TempleViewModel : ViewModel() {

    private val _templeConfig = MutableStateFlow(TempleConfig())
    val templeConfig: StateFlow<TempleConfig> = _templeConfig.asStateFlow()

    private val _templeStatus = MutableStateFlow<Map<String, SlotTelemetry>>(emptyMap())
    val templeStatus: StateFlow<Map<String, SlotTelemetry>> = _templeStatus.asStateFlow()

    private val _partyStats = MutableStateFlow(PartyStats())
    val partyStats: StateFlow<PartyStats> = _partyStats.asStateFlow()

    val isRunning: StateFlow<Boolean> = _templeStatus
        .map { map -> map.values.any { it.running } }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), false)

    private val _templeLogs = MutableStateFlow<List<LogEntry>>(emptyList())
    val templeLogs: StateFlow<List<LogEntry>> = _templeLogs.asStateFlow()

    private var unsubscribeLogs: (() -> Unit)? = null

    init {
        // Register log listener for Temple
        unsubscribeLogs = BotHelper.registerLogListener("temple") { entry ->
            _templeLogs.update { list -> (list + entry).takeLast(250) }
        }

        // Load saved configs and start polling status
        loadConfig()
        startStatusLoop()
    }

    private fun loadConfig() {
        viewModelScope.launch(Dispatchers.IO) {
            val jsonStr = BotHelper.loadConfig("temple_load_config")
            if (jsonStr != null) {
                try {
                    _templeConfig.value = BotHelper.parseTempleConfig(jsonStr)
                } catch (e: Exception) {
                    Log.e("TempleViewModel", "Error parsing temple config: ${e.message}")
                }
            }
        }
    }

    private fun startStatusLoop() {
        viewModelScope.launch(Dispatchers.IO) {
            while (isActive) {
                val statusJsonStr = BotHelper.getStatus("temple_get_status")
                if (statusJsonStr != null) {
                    _templeStatus.value = BotHelper.parseSlotTelemetryMap(statusJsonStr)
                    _partyStats.value = BotHelper.parsePartyStats(statusJsonStr)
                }
                delay(1200.milliseconds)
            }
        }
    }

    fun updateTempleSettings(server: String, roomNumber: Int, botType: String) {
        _templeConfig.update {
            it.copy(
                server = server,
                roomNumber = roomNumber,
                templeBotType = botType
            )
        }
        saveTempleConfig()
    }

    fun updateTempleSlot(slotKey: String, slotConfig: SlotConfig) {
        _templeConfig.update {
            val newSlots = it.slots.toMutableMap()
            newSlots[slotKey] = slotConfig
            it.copy(slots = newSlots)
        }
        saveTempleConfig()
    }

    fun saveTempleConfig() {
        viewModelScope.launch(Dispatchers.IO) {
            val jsonStr = BotHelper.serializeTempleConfig(_templeConfig.value)
            BotHelper.saveConfig("temple_save_config", jsonStr)
        }
    }

    fun resetTempleConfig() {
        viewModelScope.launch(Dispatchers.IO) {
            val jsonStr = BotHelper.resetConfig("temple_reset_config")
            if (jsonStr != null) {
                try {
                    _templeConfig.value = BotHelper.parseTempleConfig(jsonStr)
                } catch (e: Exception) {
                    _templeConfig.value = TempleConfig()
                }
            } else {
                _templeConfig.value = TempleConfig()
                saveTempleConfig()
            }
        }
    }

    fun startTemple(onResult: (Boolean, String?) -> Unit) {
        viewModelScope.launch(Dispatchers.IO) {
            val jsonStr = BotHelper.serializeTempleConfig(_templeConfig.value)
            val (success, error) = BotHelper.startParty("temple_start_party", jsonStr)
            withContext(Dispatchers.Main) {
                onResult(success, error)
            }
        }
    }

    fun stopTemple() {
        viewModelScope.launch(Dispatchers.IO) {
            BotHelper.stopParty("temple_stop_party")
        }
    }

    fun clearLogs(botType: String = "temple") {
        _templeLogs.value = emptyList()
    }

    override fun onCleared() {
        super.onCleared()
        unsubscribeLogs?.invoke()
    }
}
