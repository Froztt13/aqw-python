package froztt13.python.aqw.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import froztt13.python.aqw.R

val RigidSquare = FontFamily(
    Font(R.font.rigid_square, FontWeight.Normal),
    Font(R.font.rigid_square, FontWeight.Medium),
    Font(R.font.rigid_square, FontWeight.SemiBold),
    Font(R.font.rigid_square, FontWeight.Bold)
)

private val defaultTypography = Typography()

// Set of Material typography styles configured with RigidSquare
val Typography = Typography(
    displayLarge = defaultTypography.displayLarge.copy(fontFamily = RigidSquare),
    displayMedium = defaultTypography.displayMedium.copy(fontFamily = RigidSquare),
    displaySmall = defaultTypography.displaySmall.copy(fontFamily = RigidSquare),
    headlineLarge = defaultTypography.headlineLarge.copy(fontFamily = RigidSquare),
    headlineMedium = defaultTypography.headlineMedium.copy(fontFamily = RigidSquare),
    headlineSmall = defaultTypography.headlineSmall.copy(fontFamily = RigidSquare),
    titleLarge = defaultTypography.titleLarge.copy(fontFamily = RigidSquare),
    titleMedium = defaultTypography.titleMedium.copy(fontFamily = RigidSquare),
    titleSmall = defaultTypography.titleSmall.copy(fontFamily = RigidSquare),
    bodyLarge = defaultTypography.bodyLarge.copy(fontFamily = RigidSquare),
    bodyMedium = defaultTypography.bodyMedium.copy(fontFamily = RigidSquare),
    bodySmall = defaultTypography.bodySmall.copy(fontFamily = RigidSquare),
    labelLarge = defaultTypography.labelLarge.copy(fontFamily = RigidSquare),
    labelMedium = defaultTypography.labelMedium.copy(fontFamily = RigidSquare),
    labelSmall = defaultTypography.labelSmall.copy(fontFamily = RigidSquare)
)