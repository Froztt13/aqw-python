package froztt13.python.aqw.viewmodel

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import froztt13.python.aqw.data.GeneralBotConfig
import froztt13.python.aqw.data.GeneralBotTelemetry
import froztt13.python.aqw.data.GeneralSubModuleInfo
import froztt13.python.aqw.data.LogEntry
import froztt13.python.aqw.helper.BotHelper
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlin.time.Duration.Companion.milliseconds

class GeneralBotViewModel : ViewModel() {

    private val _config = MutableStateFlow(GeneralBotConfig())
    val config: StateFlow<GeneralBotConfig> = _config.asStateFlow()

    private val _telemetry = MutableStateFlow(GeneralBotTelemetry())
    val telemetry: StateFlow<GeneralBotTelemetry> = _telemetry.asStateFlow()

    val isRunning: StateFlow<Boolean> = _telemetry
        .map { it.running }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), false)

    private val _subModules = MutableStateFlow<List<GeneralSubModuleInfo>>(emptyList())
    val subModules: StateFlow<List<GeneralSubModuleInfo>> = _subModules.asStateFlow()

    private val _logs = MutableStateFlow<List<LogEntry>>(emptyList())
    val logs: StateFlow<List<LogEntry>> = _logs.asStateFlow()

    private val _errorMessage = MutableSharedFlow<String>()
    val errorMessage: SharedFlow<String> = _errorMessage.asSharedFlow()

    private var unsubscribeLogs: (() -> Unit)? = null

    init {
        // Register log listener for General Bot
        unsubscribeLogs = BotHelper.registerLogListener("general") { entry ->
            _logs.update { list -> (list + entry).takeLast(300) }
        }

        loadSubModules()
        loadConfig()
        startStatusLoop()
    }

    private fun loadSubModules() {
        viewModelScope.launch(Dispatchers.IO) {
            val jsonStr = BotHelper.getStatus("general_get_submodules")
            if (jsonStr != null) {
                val list = BotHelper.parseGeneralSubModules(jsonStr)
                if (list.isNotEmpty()) {
                    _subModules.value = list
                }
            }
        }
    }

    private fun loadConfig() {
        viewModelScope.launch(Dispatchers.IO) {
            val jsonStr = BotHelper.loadConfig("general_load_config")
            if (jsonStr != null) {
                try {
                    _config.value = BotHelper.parseGeneralBotConfig(jsonStr)
                } catch (e: Exception) {
                    Log.e("GeneralBotViewModel", "Error parsing general bot config: ${e.message}")
                }
            }
        }
    }

    private fun startStatusLoop() {
        viewModelScope.launch(Dispatchers.IO) {
            while (isActive) {
                val statusJsonStr = BotHelper.getStatus("general_get_status")
                if (statusJsonStr != null) {
                    _telemetry.value = BotHelper.parseGeneralBotTelemetry(statusJsonStr)
                }
                delay(1200.milliseconds)
            }
        }
    }

    fun updateServer(server: String) {
        _config.update { it.copy(server = server) }
        saveConfig()
    }

    fun updateRoomNumber(room: Int) {
        _config.update { it.copy(roomNumber = room) }
        saveConfig()
    }

    fun updateUsername(username: String) {
        _config.update { it.copy(username = username) }
        saveConfig()
    }

    fun updatePassword(password: String) {
        _config.update { it.copy(password = password) }
        saveConfig()
    }

    fun updateSubModule(subModuleId: String) {
        val sub = _subModules.value.find { it.id == subModuleId }
        val defaultTask = sub?.tasks?.firstOrNull()
        _config.update {
            it.copy(
                subModule = subModuleId,
                task = defaultTask?.id ?: it.task,
                targetQty = defaultTask?.defaultQty ?: it.targetQty
            )
        }
        saveConfig()
    }

    fun updateTask(taskId: String) {
        val currentSub = _subModules.value.find { it.id == _config.value.subModule }
        val task = currentSub?.tasks?.find { it.id == taskId }
        _config.update {
            it.copy(
                task = taskId,
                targetQty = task?.defaultQty ?: it.targetQty
            )
        }
        saveConfig()
    }

    fun updateTargetQty(qty: Int) {
        _config.update { it.copy(targetQty = qty.coerceAtLeast(1)) }
        saveConfig()
    }

    fun updateSoloClass(cls: String) {
        _config.update { it.copy(soloClass = cls) }
        saveConfig()
    }

    fun updateFarmClass(cls: String) {
        _config.update { it.copy(farmClass = cls) }
        saveConfig()
    }

    fun saveConfig() {
        val current = _config.value
        viewModelScope.launch(Dispatchers.IO) {
            val jsonStr = BotHelper.serializeGeneralBotConfig(current)
            BotHelper.saveConfig("general_save_config", jsonStr)
        }
    }

    fun resetConfig() {
        viewModelScope.launch(Dispatchers.IO) {
            val jsonStr = BotHelper.resetConfig("general_reset_config")
            if (jsonStr != null) {
                _config.value = BotHelper.parseGeneralBotConfig(jsonStr)
            }
        }
    }

    fun resetState() {
        viewModelScope.launch(Dispatchers.IO) {
            BotHelper.resetState("general_reset_state")
            _telemetry.update {
                it.copy(
                    running = false,
                    isConnected = false,
                    status = "Idle",
                    message = "State reset by user",
                    cooldowns = emptyMap()
                )
            }
        }
    }

    fun clearLogs() {
        _logs.value = emptyList()
    }

    fun startBot(onStarted: () -> Unit = {}) {
        val current = _config.value
        if (current.username.isBlank()) {
            viewModelScope.launch {
                _errorMessage.emit("Username cannot be empty")
            }
            return
        }
        if (current.password.isBlank()) {
            viewModelScope.launch {
                _errorMessage.emit("Password cannot be empty")
            }
            return
        }

        viewModelScope.launch(Dispatchers.IO) {
            val jsonStr = BotHelper.serializeGeneralBotConfig(current)
            val (success, error) = BotHelper.startParty("general_start", jsonStr)
            if (success) {
                withContext(Dispatchers.Main) {
                    onStarted()
                }
            } else {
                _errorMessage.emit(error ?: "Failed to start General Bot")
            }
        }
    }

    fun stopBot() {
        viewModelScope.launch(Dispatchers.IO) {
            BotHelper.stopParty("general_stop")
        }
    }

    override fun onCleared() {
        super.onCleared()
        unsubscribeLogs?.invoke()
        unsubscribeLogs = null
    }
}
