package froztt13.python.aqw.viewmodel

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import froztt13.python.aqw.data.EclipseConfig
import froztt13.python.aqw.data.LogEntry
import froztt13.python.aqw.data.PartyStats
import froztt13.python.aqw.data.SlotConfig
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

class EclipseViewModel : ViewModel() {

    private val _eclipseConfig = MutableStateFlow(EclipseConfig())
    val eclipseConfig: StateFlow<EclipseConfig> = _eclipseConfig.asStateFlow()

    private val _eclipseStatus = MutableStateFlow<Map<String, SlotTelemetry>>(emptyMap())
    val eclipseStatus: StateFlow<Map<String, SlotTelemetry>> = _eclipseStatus.asStateFlow()

    private val _partyStats = MutableStateFlow(PartyStats())
    val partyStats: StateFlow<PartyStats> = _partyStats.asStateFlow()

    val isRunning: StateFlow<Boolean> = _eclipseStatus
        .map { map -> map.values.any { it.running } }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), false)

    private val _eclipseLogs = MutableStateFlow<List<LogEntry>>(emptyList())
    val eclipseLogs: StateFlow<List<LogEntry>> = _eclipseLogs.asStateFlow()

    private var unsubscribeLogs: (() -> Unit)? = null

    init {
        // Register log listener for Eclipse
        unsubscribeLogs = BotHelper.registerLogListener("eclipse") { entry ->
            _eclipseLogs.update { list -> (list + entry).takeLast(250) }
        }

        // Load saved configs and start polling status
        loadConfig()
        startStatusLoop()
    }

    private fun loadConfig() {
        viewModelScope.launch(Dispatchers.IO) {
            val jsonStr = BotHelper.loadConfig("eclipse_load_config")
            if (jsonStr != null) {
                try {
                    _eclipseConfig.value = BotHelper.parseEclipseConfig(jsonStr)
                } catch (e: Exception) {
                    Log.e("EclipseViewModel", "Error parsing eclipse config: ${e.message}")
                }
            }
        }
    }

    private fun startStatusLoop() {
        viewModelScope.launch(Dispatchers.IO) {
            while (isActive) {
                val statusJsonStr = BotHelper.getStatus("eclipse_get_status")
                if (statusJsonStr != null) {
                    _eclipseStatus.value = BotHelper.parseSlotTelemetryMap(statusJsonStr)
                    _partyStats.value = BotHelper.parsePartyStats(statusJsonStr)
                }
                delay(1200.milliseconds)
            }
        }
    }

    fun updateEclipseSettings(server: String, roomNumber: Int) {
        _eclipseConfig.update { it.copy(server = server, roomNumber = roomNumber) }
        saveEclipseConfig()
    }

    fun updateEclipseSlot(slotKey: String, slotConfig: SlotConfig) {
        _eclipseConfig.update {
            val newSlots = it.slots.toMutableMap()
            newSlots[slotKey] = slotConfig
            it.copy(slots = newSlots)
        }
        saveEclipseConfig()
    }

    fun saveEclipseConfig() {
        viewModelScope.launch(Dispatchers.IO) {
            val jsonStr = BotHelper.serializeEclipseConfig(_eclipseConfig.value)
            BotHelper.saveConfig("eclipse_save_config", jsonStr)
        }
    }

    fun resetEclipseConfig() {
        viewModelScope.launch(Dispatchers.IO) {
            val jsonStr = BotHelper.resetConfig("eclipse_reset_config")
            if (jsonStr != null) {
                try {
                    _eclipseConfig.value = BotHelper.parseEclipseConfig(jsonStr)
                } catch (e: Exception) {
                    _eclipseConfig.value = EclipseConfig()
                }
            } else {
                _eclipseConfig.value = EclipseConfig()
                saveEclipseConfig()
            }
        }
    }

    fun startEclipse(onResult: (Boolean, String?) -> Unit) {
        viewModelScope.launch(Dispatchers.IO) {
            val jsonStr = BotHelper.serializeEclipseConfig(_eclipseConfig.value)
            val (success, error) = BotHelper.startParty("eclipse_start_party", jsonStr)
            withContext(Dispatchers.Main) {
                onResult(success, error)
            }
        }
    }

    fun stopEclipse() {
        viewModelScope.launch(Dispatchers.IO) {
            BotHelper.stopParty("eclipse_stop_party")
        }
    }

    fun clearLogs(botType: String = "eclipse") {
        _eclipseLogs.value = emptyList()
    }

    override fun onCleared() {
        super.onCleared()
        unsubscribeLogs?.invoke()
    }
}
