package froztt13.python.aqw.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import froztt13.python.aqw.data.HubOverview
import froztt13.python.aqw.helper.BotHelper
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlin.time.Duration.Companion.milliseconds

class DashboardViewModel : ViewModel() {

    private val _hubOverview = MutableStateFlow(HubOverview())
    val hubOverview: StateFlow<HubOverview> = _hubOverview.asStateFlow()

    init {
        startStatusLoop()
    }

    private fun startStatusLoop() {
        viewModelScope.launch(Dispatchers.IO) {
            while (isActive) {
                try {
                    val status = BotHelper.getHubStatus()
                    _hubOverview.value = status
                } catch (_: Exception) {
                }
                delay(1200.milliseconds)
            }
        }
    }

    fun refreshStatus() {
        viewModelScope.launch(Dispatchers.IO) {
            try {
                _hubOverview.value = BotHelper.getHubStatus()
            } catch (_: Exception) {
            }
        }
    }
}
