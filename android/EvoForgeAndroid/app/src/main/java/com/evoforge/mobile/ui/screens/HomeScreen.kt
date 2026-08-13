package com.evoforge.mobile.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Cloud
import androidx.compose.material.icons.outlined.Memory
import androidx.compose.material.icons.outlined.Schedule
import androidx.compose.material.icons.rounded.CheckCircle
import androidx.compose.material.icons.rounded.Groups
import androidx.compose.material.icons.rounded.PlayArrow
import androidx.compose.material.icons.rounded.Storage
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import com.evoforge.mobile.ui.theme.*
import com.evoforge.mobile.viewmodel.ConnectionState
import com.evoforge.mobile.viewmodel.SystemViewModel

@Composable
fun HomeScreen(systemViewModel: SystemViewModel) {
    val connectionState by systemViewModel.connectionState.collectAsState()
    val systemStatus by systemViewModel.systemStatus.collectAsState()
    val computePolicy by systemViewModel.computePolicy.collectAsState()

    val isOnline = connectionState is ConnectionState.Online
    val statusDotColor = when (connectionState) {
        is ConnectionState.Online -> StatusOnline
        is ConnectionState.Connecting -> StatusWarning
        else -> StatusError
    }

    val controlPlaneStatusStr = when (connectionState) {
        is ConnectionState.Online -> "ONLINE"
        is ConnectionState.Connecting -> "CONNECTING"
        is ConnectionState.NotConfigured -> "NOT CONFIGURED"
        is ConnectionState.Offline -> "OFFLINE"
    }

    val controlPlaneColor = when (connectionState) {
        is ConnectionState.Online -> StatusOnline
        is ConnectionState.Connecting -> StatusWarning
        is ConnectionState.NotConfigured -> TextTertiaryDark
        is ConnectionState.Offline -> StatusError
    }

    val computeModeStr = computePolicy?.mode ?: systemStatus?.compute_mode ?: "UNKNOWN"

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .verticalScroll(rememberScrollState())
            .padding(20.dp)
    ) {
        // Header
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.padding(bottom = 4.dp)
        ) {
            // Status dot
            Box(
                modifier = Modifier
                    .size(10.dp)
                    .clip(CircleShape)
                    .background(statusDotColor)
            )
            Spacer(modifier = Modifier.width(10.dp))
            Text(
                "EvoForge",
                style = MaterialTheme.typography.headlineLarge
            )
        }
        Text(
            "Mission Control",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(bottom = 28.dp)
        )

        // System Status Section
        Text(
            "SYSTEM STATUS",
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(bottom = 12.dp)
        )

        SystemStatusRow(
            icon = Icons.Outlined.Cloud,
            label = "Control Plane",
            status = controlPlaneStatusStr,
            statusColor = controlPlaneColor
        )
        Spacer(modifier = Modifier.height(8.dp))
        SystemStatusRow(
            icon = Icons.Outlined.Schedule,
            label = "Scheduler",
            status = if (isOnline) systemStatus?.system_state?.uppercase() ?: "UNKNOWN" else "UNKNOWN",
            statusColor = if (isOnline) StatusOnline else TextTertiaryDark
        )
        Spacer(modifier = Modifier.height(8.dp))
        SystemStatusRow(
            icon = Icons.Outlined.Memory,
            label = "Compute Mode",
            status = computeModeStr,
            statusColor = if (isOnline) StatusInfo else TextTertiaryDark
        )

        Spacer(modifier = Modifier.height(32.dp))

        // Quick Stats
        Text(
            "OVERVIEW",
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(bottom = 12.dp)
        )

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            StatCard(
                modifier = Modifier.weight(1f),
                icon = Icons.Rounded.PlayArrow,
                value = if (isOnline) "${systemStatus?.active_workflows ?: 0}" else "-",
                label = "Workflows",
                accentColor = if (isOnline) StatusRunning else TextTertiaryDark
            )
            StatCard(
                modifier = Modifier.weight(1f),
                icon = Icons.Rounded.CheckCircle,
                value = if (isOnline) "${systemStatus?.complete_workflows ?: 0}" else "-",
                label = "Completed",
                accentColor = if (isOnline) StatusOnline else TextTertiaryDark
            )
        }
        Spacer(modifier = Modifier.height(12.dp))
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            StatCard(
                modifier = Modifier.weight(1f),
                icon = Icons.Rounded.Storage,
                value = if (isOnline) "${systemStatus?.healthy_executors ?: 0}" else "-",
                label = "Healthy Execs",
                accentColor = if (isOnline) StatusInfo else TextTertiaryDark
            )
            StatCard(
                modifier = Modifier.weight(1f),
                icon = Icons.Rounded.Groups,
                value = if (isOnline) "${systemStatus?.unhealthy_executors ?: 0}" else "-",
                label = "Unhealthy",
                accentColor = if (isOnline) StatusWarning else TextTertiaryDark
            )
        }

        Spacer(modifier = Modifier.height(32.dp))

        // Recent Activity
        Text(
            "RECENT ACTIVITY",
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(bottom = 12.dp)
        )

        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
            color = MaterialTheme.colorScheme.surface,
            border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outline)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                if (connectionState is ConnectionState.NotConfigured) {
                    Text(
                        "No connection",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        "Configure your Control Plane in Settings",
                        style = MaterialTheme.typography.bodySmall,
                        color = TextTertiaryDark
                    )
                } else if (connectionState is ConnectionState.Offline) {
                    Text(
                        "Connection Error",
                        style = MaterialTheme.typography.bodyMedium,
                        color = StatusError
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        (connectionState as ConnectionState.Offline).reason,
                        style = MaterialTheme.typography.bodySmall,
                        color = TextTertiaryDark
                    )
                } else {
                    Text(
                        "No recent events",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }
    }
}

@Composable
fun SystemStatusRow(
    icon: ImageVector,
    label: String,
    status: String,
    statusColor: Color
) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        color = MaterialTheme.colorScheme.surface,
        border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outline)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 14.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.width(12.dp))
                Text(
                    label,
                    style = MaterialTheme.typography.titleMedium
                )
            }
            Surface(
                shape = RoundedCornerShape(6.dp),
                color = statusColor.copy(alpha = 0.12f)
            ) {
                Text(
                    status,
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                    style = MaterialTheme.typography.labelMedium,
                    color = statusColor
                )
            }
        }
    }
}

@Composable
fun StatCard(
    modifier: Modifier = Modifier,
    icon: ImageVector,
    value: String,
    label: String,
    accentColor: Color
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        color = MaterialTheme.colorScheme.surface,
        border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outline)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(32.dp)
                        .clip(RoundedCornerShape(8.dp))
                        .background(accentColor.copy(alpha = 0.12f)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = icon,
                        contentDescription = null,
                        tint = accentColor,
                        modifier = Modifier.size(18.dp)
                    )
                }
            }
            Spacer(modifier = Modifier.height(14.dp))
            Text(
                value,
                style = MaterialTheme.typography.headlineMedium
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                label,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
