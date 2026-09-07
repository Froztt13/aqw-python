package froztt13.python.aqw.viewmodel

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import froztt13.python.aqw.data.DoomAccount
import froztt13.python.aqw.data.LogEntry
import froztt13.python.aqw.data.WeeklyDoomConfig
import froztt13.python.aqw.data.WeeklyDoomTelemetry
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

class WeeklyDoomViewModel : ViewModel() {

    private val _doomConfig = MutableStateFlow(WeeklyDoomConfig())
    val doomConfig: StateFlow<WeeklyDoomConfig> = _doomConfig.asStateFlow()

    private val _doomStatus = MutableStateFlow(WeeklyDoomTelemetry())
    val doomStatus: StateFlow<WeeklyDoomTelemetry> = _doomStatus.asStateFlow()

    val isRunning: StateFlow<Boolean> = _doomStatus
        .map { it.running }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), false)

    private val _doomLogs = MutableStateFlow<List<LogEntry>>(emptyList())
    val doomLogs: StateFlow<List<LogEntry>> = _doomLogs.asStateFlow()

    private val _errorMessage = MutableSharedFlow<String>()
    val errorMessage: SharedFlow<String> = _errorMessage.asSharedFlow()

    private var unsubscribeLogs: (() -> Unit)? = null

    init {
        // Register log listener for Weekly Doom
        unsubscribeLogs = BotHelper.registerLogListener("doom") { entry ->
            _doomLogs.update { list -> (list + entry).takeLast(300) }
        }

        // Load saved configs and start polling status
        loadConfig()
        startStatusLoop()
    }

    private fun loadConfig() {
        viewModelScope.launch(Dispatchers.IO) {
            val jsonStr = BotHelper.loadConfig("doom_load_config")
            if (jsonStr != null) {
                try {
                    _doomConfig.value = BotHelper.parseWeeklyDoomConfig(jsonStr)
                } catch (e: Exception) {
                    Log.e("WeeklyDoomViewModel", "Error parsing doom config: ${e.message}")
                }
            }
        }
    }

    private fun startStatusLoop() {
        viewModelScope.launch(Dispatchers.IO) {
            while (isActive) {
                val statusJsonStr = BotHelper.getStatus("doom_get_status")
                if (statusJsonStr != null) {
                    _doomStatus.value = BotHelper.parseWeeklyDoomTelemetry(statusJsonStr)
                }
                delay(1200.milliseconds)
            }
        }
    }

    fun updateServer(server: String) {
        _doomConfig.update { it.copy(server = server) }
        saveDoomConfig()
    }

    fun addAccount(username: String = "", password: String = "") {
        _doomConfig.update {
            val currentAccounts =
                it.accounts.filter { acc -> acc.username.isNotBlank() }.toMutableList()
            currentAccounts.add(DoomAccount(username = username, password = password))
            it.copy(accounts = currentAccounts)
        }
        saveDoomConfig()
    }

    fun removeAccount(id: String) {
        _doomConfig.update {
            val currentAccounts = it.accounts.filter { acc -> acc.id != id }
            it.copy(accounts = currentAccounts)
        }
        saveDoomConfig()
    }

    fun updateAccount(id: String, username: String, password: String) {
        _doomConfig.update {
            val currentAccounts = it.accounts.map { acc ->
                if (acc.id == id) {
                    acc.copy(username = username, password = password)
                } else {
                    acc
                }
            }
            it.copy(accounts = currentAccounts)
        }
        saveDoomConfig()
    }

    fun toggleAccount(id: String, enabled: Boolean) {
        _doomConfig.update {
            val currentAccounts = it.accounts.map { acc ->
                if (acc.id == id) {
                    acc.copy(enabled = enabled)
                } else {
                    acc
                }
            }
            it.copy(accounts = currentAccounts)
        }
        saveDoomConfig()
    }

    fun updateAccountsOrder(newAccounts: List<DoomAccount>) {
        _doomConfig.update { it.copy(accounts = newAccounts) }
        saveDoomConfig()
    }

    fun moveAccount(fromIndex: Int, toIndex: Int) {
        _doomConfig.update { config ->
            if (fromIndex !in config.accounts.indices || toIndex !in config.accounts.indices || fromIndex == toIndex) {
                return@update config
            }
            val currentAccounts = config.accounts.toMutableList()
            val item = currentAccounts.removeAt(fromIndex)
            currentAccounts.add(toIndex, item)
            config.copy(accounts = currentAccounts)
        }
        saveDoomConfig()
    }

    fun saveDoomConfig() {
        viewModelScope.launch(Dispatchers.IO) {
            val jsonStr = BotHelper.serializeWeeklyDoomConfig(_doomConfig.value)
            BotHelper.saveConfig("doom_save_config", jsonStr)
        }
    }

    fun resetDoomConfig() {
        viewModelScope.launch(Dispatchers.IO) {
            val jsonStr = BotHelper.resetConfig("doom_reset_config")
            if (jsonStr != null) {
                try {
                    _doomConfig.value = BotHelper.parseWeeklyDoomConfig(jsonStr)
                } catch (e: Exception) {
                    _doomConfig.value = WeeklyDoomConfig()
                }
            } else {
                _doomConfig.value = WeeklyDoomConfig()
                saveDoomConfig()
            }
        }
    }

    fun startDoom(onResult: (Boolean, String?) -> Unit) {
        val enabledWithUser = _doomConfig.value.accounts.filter {
            it.enabled && it.username.isNotBlank()
        }
        if (enabledWithUser.isEmpty()) {
            val err = "Please configure at least one enabled account with a valid username"
            viewModelScope.launch {
                _errorMessage.emit(err)
            }
            onResult(false, err)
            return
        }

        viewModelScope.launch(Dispatchers.IO) {
            val jsonStr = BotHelper.serializeWeeklyDoomConfig(_doomConfig.value)
            val (success, error) = BotHelper.startParty("doom_start", jsonStr)
            if (!success && error != null) {
                _errorMessage.emit(error)
            }
            withContext(Dispatchers.Main) {
                onResult(success, error)
            }
        }
    }

    fun stopDoom() {
        viewModelScope.launch(Dispatchers.IO) {
            BotHelper.stopParty("doom_stop")
        }
    }

    fun clearLogs() {
        _doomLogs.value = emptyList()
    }

    override fun onCleared() {
        super.onCleared()
        unsubscribeLogs?.invoke()
    }
}
