package froztt13.python.aqw.viewmodel

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import froztt13.python.aqw.data.LogEntry
import froztt13.python.aqw.data.PartyStats
import froztt13.python.aqw.data.SlaveSlotConfig
import froztt13.python.aqw.data.SlaveryConfig
import froztt13.python.aqw.data.SlotTelemetry
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

class SlaveryViewModel : ViewModel() {

    private val _slaveryConfig = MutableStateFlow(SlaveryConfig())
    val slaveryConfig: StateFlow<SlaveryConfig> = _slaveryConfig.asStateFlow()

    private val _slaveryStatus = MutableStateFlow<Map<String, SlotTelemetry>>(emptyMap())
    val slaveryStatus: StateFlow<Map<String, SlotTelemetry>> = _slaveryStatus.asStateFlow()

    private val _partyStats = MutableStateFlow(PartyStats())
    val partyStats: StateFlow<PartyStats> = _partyStats.asStateFlow()

    val isRunning: StateFlow<Boolean> = _slaveryStatus
        .map { map -> map.values.any { it.running } }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), false)

    private val _slaveryLogs = MutableStateFlow<List<LogEntry>>(emptyList())
    val slaveryLogs: StateFlow<List<LogEntry>> = _slaveryLogs.asStateFlow()

    private var unsubscribeLogs: (() -> Unit)? = null

    init {
        unsubscribeLogs = BotHelper.registerLogListener("slavery") { entry ->
            _slaveryLogs.update { list -> (list + entry).takeLast(300) }
        }

        loadConfig()
        startStatusLoop()
    }

    private fun loadConfig() {
        viewModelScope.launch(Dispatchers.IO) {
            val jsonStr = BotHelper.loadConfig("slavery_load_config")
            if (jsonStr != null) {
                try {
                    _slaveryConfig.value = BotHelper.parseSlaveryConfig(jsonStr)
                } catch (e: Exception) {
                    Log.e("SlaveryViewModel", "Error parsing slavery config: ${e.message}")
                }
            }
        }
    }

    private fun startStatusLoop() {
        viewModelScope.launch(Dispatchers.IO) {
            while (isActive) {
                val statusJsonStr = BotHelper.getStatus("slavery_get_status")
                if (statusJsonStr != null) {
                    _slaveryStatus.value = BotHelper.parseSlotTelemetryMap(statusJsonStr)
                    _partyStats.value = BotHelper.parsePartyStats(statusJsonStr)
                }
                delay(1200.milliseconds)
            }
        }
    }

    fun updateGlobalSettings(
        server: String,
        followPlayer: String,
        defaultRoomNumber: Int,
        copyWalk: Boolean,
        autoZone: String,
        targetsPriority: String,
        whitelist: String,
        lockedZones: List<String>
    ) {
        _slaveryConfig.update {
            it.copy(
                server = server,
                followPlayer = followPlayer,
                defaultRoomNumber = defaultRoomNumber,
                copyWalk = copyWalk,
                autoZone = autoZone,
                targetsPriority = targetsPriority,
                whitelist = whitelist,
                lockedZones = lockedZones
            )
        }
        saveSlaveryConfig()
    }

    fun updateSlot(slotKey: String, slotConfig: SlaveSlotConfig) {
        _slaveryConfig.update {
            val newSlots = it.slots.toMutableMap()
            newSlots[slotKey] = slotConfig
            it.copy(slots = newSlots)
        }
        saveSlaveryConfig()
    }

    fun saveSlaveryConfig() {
        viewModelScope.launch(Dispatchers.IO) {
            val jsonStr = BotHelper.serializeSlaveryConfig(_slaveryConfig.value)
            BotHelper.saveConfig("slavery_save_config", jsonStr)
        }
    }

    fun resetSlaveryConfig() {
        viewModelScope.launch(Dispatchers.IO) {
            val jsonStr = BotHelper.resetConfig("slavery_reset_config")
            if (jsonStr != null) {
                try {
                    _slaveryConfig.value = BotHelper.parseSlaveryConfig(jsonStr)
                } catch (e: Exception) {
                    _slaveryConfig.value = SlaveryConfig()
                }
            } else {
                _slaveryConfig.value = SlaveryConfig()
                saveSlaveryConfig()
            }
        }
    }

    fun startSlavery(onResult: (Boolean, String?) -> Unit) {
        viewModelScope.launch(Dispatchers.IO) {
            val jsonStr = BotHelper.serializeSlaveryConfig(_slaveryConfig.value)
            val (success, error) = BotHelper.startParty("slavery_start_party", jsonStr)
            withContext(Dispatchers.Main) {
                onResult(success, error)
            }
        }
    }

    fun stopSlavery() {
        viewModelScope.launch(Dispatchers.IO) {
            BotHelper.stopParty("slavery_stop_party")
        }
    }

    fun clearLogs() {
        _slaveryLogs.value = emptyList()
    }

    override fun onCleared() {
        super.onCleared()
        unsubscribeLogs?.invoke()
    }
}
