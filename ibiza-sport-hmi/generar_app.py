import os

archivos = {
    "settings.gradle.kts": """pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "IbizaSportHMI"
include(":app")
""",

    "build.gradle.kts": """plugins {
    id("com.android.application") version "8.4.0" apply false
    id("org.jetbrains.kotlin.android") version "1.9.24" apply false
}
""",

    "gradle.properties": """org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
kotlin.code.style=official
android.nonTransitiveRClass=true
""",

    "app/build.gradle.kts": """plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.ibiza.sporthmi"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.ibiza.sporthmi"
        minSdk = 29
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.lifecycle:lifecycle-common-java8:2.7.0")
    implementation("androidx.car.app:app:1.4.0")
    implementation("androidx.car.app:app-projected:1.4.0")
}
""",

    "app/src/main/res/xml/automotive_app_desc.xml": """<?xml version="1.0" encoding="utf-8"?>
<automotiveApp>
    <uses name="template" />
</automotiveApp>
""",

    "app/src/main/res/drawable/ic_sport_icon.xml": """<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path
        android:fillColor="#121318"
        android:pathData="M0,0h108v108h-108z"/>
    <path
        android:strokeColor="#E32636"
        android:strokeWidth="6"
        android:strokeLineCap="round"
        android:pathData="M26,74 A36,36 0 1,1 82,74"/>
    <path
        android:strokeColor="#FFFFFF"
        android:strokeWidth="4"
        android:strokeLineCap="round"
        android:pathData="M54,54 L74,36"/>
    <path
        android:fillColor="#E32636"
        android:pathData="M54,54m-6,0a6,6 0,1 1,12 0a6,6 0,1 1,-12 0"/>
</vector>
""",

    "app/src/main/AndroidManifest.xml": """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
    <uses-permission android:name="androidx.car.app.NAVIGATION_TEMPLATES" />
    <uses-permission android:name="androidx.car.app.ACCESS_SURFACE" />

    <application
        android:allowBackup="true"
        android:icon="@drawable/ic_sport_icon"
        android:label="Ibiza Sport HMI"
        android:supportsRtl="true"
        android:theme="@android:style/Theme.DeviceDefault.NoActionBar">

        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <meta-data
            android:name="com.google.android.gms.car.application"
            android:resource="@xml/automotive_app_desc" />
        <meta-data
            android:name="androidx.car.app.minCarApiLevel"
            android:value="1" />

        <service
            android:name=".SportCarService"
            android:exported="true">
            <intent-filter>
                <action android:name="androidx.car.app.CarAppService" />
                <category android:name="androidx.car.app.category.NAVIGATION" />
            </intent-filter>
        </service>

    </application>
</manifest>
""",

    "app/src/main/java/com/ibiza/sporthmi/MainActivity.kt": """package com.ibiza.sporthmi

import android.Manifest
import android.app.Activity
import android.content.pm.PackageManager
import android.graphics.Color
import android.graphics.Typeface
import android.os.Bundle
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView

class MainActivity : Activity() {
    private lateinit var statusText: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setBackgroundColor(Color.parseColor("#0B0C10"))
            setPadding(64, 64, 64, 64)
        }

        val title = TextView(this).apply {
            text = "SEAT IBIZA SPORT HMI"
            textSize = 24f
            setTextColor(Color.parseColor("#E32636"))
            typeface = Typeface.DEFAULT_BOLD
            gravity = Gravity.CENTER
        }

        statusText = TextView(this).apply {
            textSize = 16f
            setTextColor(Color.WHITE)
            gravity = Gravity.CENTER
            setPadding(0, 40, 0, 60)
        }

        val btnPermiso = Button(this).apply {
            text = "ACTIVAR PERMISO DE VELOCÍMETRO GPS"
            setBackgroundColor(Color.parseColor("#E32636"))
            setTextColor(Color.WHITE)
            setPadding(40, 25, 40, 25)
            setOnClickListener { solicitarPermisos() }
        }

        layout.addView(title)
        layout.addView(statusText)
        layout.addView(btnPermiso)
        setContentView(layout)

        actualizarEstado()
        solicitarPermisos()
    }

    private fun solicitarPermisos() {
        requestPermissions(
            arrayOf(
                Manifest.permission.ACCESS_FINE_LOCATION,
                Manifest.permission.ACCESS_COARSE_LOCATION
            ),
            101
        )
    }

    private fun actualizarEstado() {
        val concedido = checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
        statusText.text = if (concedido) {
            "Permiso GPS Activo.\\n\\nConecta tu celular al SEAT Ibiza y abre 'Ibiza Sport HMI' en la pantalla de Android Auto."
        } else {
            "Se requiere permiso de Ubicación para medir la velocidad por GPS y la altitud en tiempo real."
        }
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        actualizarEstado()
    }
}
""",

    "app/src/main/java/com/ibiza/sporthmi/SportCarService.kt": """package com.ibiza.sporthmi

import android.content.Context
import android.content.Intent
import android.graphics.*
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import androidx.car.app.*
import androidx.car.app.model.*
import androidx.car.app.navigation.model.NavigationTemplate
import androidx.car.app.validation.HostValidator
import androidx.lifecycle.DefaultLifecycleObserver
import androidx.lifecycle.LifecycleOwner
import kotlin.math.*

class SportCarService : CarAppService() {
    override fun createHostValidator(): HostValidator = HostValidator.ALLOW_ALL_HOSTS_VALIDATOR
    override fun onCreateSession(): Session = SportDashSession()
}

class SportDashSession : Session() {
    override fun onCreateScreen(intent: Intent): Screen = SportDashScreen(carContext)
}

class SportDashScreen(carContext: CarContext) : Screen(carContext), SurfaceCallback, LocationListener, SensorEventListener {

    private var surfaceContainer: SurfaceContainer? = null
    private val handler = Handler(Looper.getMainLooper())
    private var isRendering = false

    // Temas de color: 0 = Rojo FR, 1 = Cobre Cupra, 2 = Azul Sport
    private var themeIndex = 0
    private val themeColors = listOf(
        Color.parseColor("#E32636"), // Rojo FR
        Color.parseColor("#C87D55"), // Cobre Cupra
        Color.parseColor("#00A8E8")  // Azul Sport
    )
    private val themeNames = listOf("Rojo FR", "Cobre", "Azul")

    // Telemetría en tiempo real
    private var targetSpeedKmh = 0f
    private var displayedSpeedKmh = 0f
    private var maxSpeedKmh = 0f
    private var altitudeMeters = 0.0
    private var bearingDegrees = 0f

    // Fuerzas G
    private var gForceX = 0f
    private var gForceY = 0f
    private var maxGForce = 0f

    // Cronómetro 0-100 km/h
    private var chronoStartTime = 0L
    private var isChronoRunning = false
    private var bestZeroToHundredSec = 0f

    // Pinceles gráficos
    private val bgPaint = Paint().apply { color = Color.parseColor("#090A0F") }
    private val dialRingPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#1F2330")
        style = Paint.Style.STROKE
        strokeWidth = 22f
        strokeCap = Paint.Cap.ROUND
    }
    private val activeArcPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = themeColors[0]
        style = Paint.Style.STROKE
        strokeWidth = 22f
        strokeCap = Paint.Cap.ROUND
    }
    private val tickPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#A0A8B8")
        strokeWidth = 3f
    }
    private val needlePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.WHITE
        strokeWidth = 7f
        strokeCap = Paint.Cap.ROUND
    }
    private val bigSpeedPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.WHITE
        textSize = 92f
        typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
        textAlign = Paint.Align.CENTER
    }
    private val labelPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#8C92AC")
        textSize = 22f
        typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
        textAlign = Paint.Align.CENTER
    }
    private val valuePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.WHITE
        textSize = 28f
        typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
        textAlign = Paint.Align.CENTER
    }

    init {
        lifecycle.addObserver(object : DefaultLifecycleObserver {
            override fun onStart(owner: LifecycleOwner) {
                carContext.getCarService(AppManager::class.java).setSurfaceCallback(this@SportDashScreen)
                iniciarSensores()
            }
            override fun onStop(owner: LifecycleOwner) {
                detenerSensores()
                isRendering = false
            }
        })
    }

    @Suppress("MissingPermission")
    private fun iniciarSensores() {
        try {
            val locManager = carContext.getSystemService(Context.LOCATION_SERVICE) as LocationManager
            locManager.requestLocationUpdates(LocationManager.GPS_PROVIDER, 150L, 0f, this)

            val sensorManager = carContext.getSystemService(Context.SENSOR_SERVICE) as SensorManager
            val accel = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
            sensorManager.registerListener(this, accel, SensorManager.SENSOR_DELAY_GAME)
        } catch (_: SecurityException) {}
    }

    private fun detenerSensores() {
        try {
            val locManager = carContext.getSystemService(Context.LOCATION_SERVICE) as LocationManager
            locManager.removeUpdates(this)
            val sensorManager = carContext.getSystemService(Context.SENSOR_SERVICE) as SensorManager
            sensorManager.unregisterListener(this)
        } catch (_: Exception) {}
    }

    private val renderLoop = object : Runnable {
        override fun run() {
            // Interpolación suave de la aguja
            displayedSpeedKmh += (targetSpeedKmh - displayedSpeedKmh) * 0.22f
            dibujarFrame()
            if (isRendering) {
                handler.postDelayed(this, 33L)
            }
        }
    }

    override fun onSurfaceAvailable(surfaceContainer: SurfaceContainer) {
        this.surfaceContainer = surfaceContainer
        isRendering = true
        handler.post(renderLoop)
    }

    override fun onSurfaceDestroyed(surfaceContainer: SurfaceContainer) {
        isRendering = false
        this.surfaceContainer = null
    }

    private fun dibujarFrame() {
        val surface = surfaceContainer?.surface ?: return
        if (!surface.isValid) return

        val canvas = surface.lockCanvas(null) ?: return
        try {
            val w = canvas.width.toFloat()
            val h = canvas.height.toFloat()
            val accentColor = themeColors[themeIndex]
            activeArcPaint.color = accentColor

            // Fondo general oscuro
            canvas.drawRect(0f, 0f, w, h, bgPaint)

            val centerY = h * 0.55f
            val mainRadius = min(w, h) * 0.35f
            val sideRadius = mainRadius * 0.68f

            // 1. RELOJ CENTRAL: VELOCÍMETRO (0 - 240 KM/H)
            val centerX = w * 0.50f
            dibujarVelocimetro(canvas, centerX, centerY, mainRadius, accentColor)

            // 2. RELOJ IZQUIERDO: RADAR G-FORCE Y 0-100 KM/H
            val leftX = w * 0.19f
            dibujarRadarG(canvas, leftX, centerY, sideRadius, accentColor)

            // 3. RELOJ DERECHO: ALTÍMETRO, BRÚJULA Y POTENCIA G
            val rightX = w * 0.81f
            dibujarTelemetriaDerecha(canvas, rightX, centerY, sideRadius, accentColor)

        } finally {
            surface.unlockCanvasAndPost(canvas)
        }
    }

    private fun dibujarVelocimetro(canvas: Canvas, cx: Float, cy: Float, r: Float, accent: Int) {
        val rect = RectF(cx - r, cy - r, cx + r, cy + r)
        canvas.drawArc(rect, 150f, 240f, false, dialRingPaint)

        val sweep = (displayedSpeedKmh.coerceIn(0f, 240f) / 240f) * 240f
        canvas.drawArc(rect, 150f, sweep, false, activeArcPaint)

        // Marcas graduadas cada 10 km/h y números cada 40 km/h
        val numPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE
            textSize = 20f
            textAlign = Paint.Align.CENTER
            typeface = Typeface.DEFAULT_BOLD
        }
        for (speed in 0..240 step 10) {
            val angleDeg = 150f + (speed / 240f) * 240f
            val rad = Math.toRadians(angleDeg.toDouble())
            val isMajor = speed % 20 == 0
            val startR = if (isMajor) r - 28f else r - 18f
            val endR = r - 10f

            val x1 = cx + (startR * cos(rad)).toFloat()
            val y1 = cy + (startR * sin(rad)).toFloat()
            val x2 = cx + (endR * cos(rad)).toFloat()
            val y2 = cy + (endR * sin(rad)).toFloat()

            tickPaint.strokeWidth = if (isMajor) 4f else 2f
            canvas.drawLine(x1, y1, x2, y2, tickPaint)

            if (speed % 40 == 0) {
                val textR = r - 48f
                val tx = cx + (textR * cos(rad)).toFloat()
                val ty = cy + (textR * sin(rad)).toFloat() + 7f
                canvas.drawText("$speed", tx, ty, numPaint)
            }
        }

        // Aguja del velocímetro
        val needleAngle = Math.toRadians((150f + sweep).toDouble())
        val nx = cx + ((r - 22f) * cos(needleAngle)).toFloat()
        val ny = cy + ((r - 22f) * sin(needleAngle)).toFloat()
        needlePaint.color = accent
        canvas.drawLine(cx, cy, nx, ny, needlePaint)
        canvas.drawCircle(cx, cy, 14f, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.WHITE })

        // Lectura digital central inferior
        canvas.drawText("${displayedSpeedKmh.roundToInt()}", cx, cy + r * 0.48f, bigSpeedPaint)
        canvas.drawText("KM/H", cx, cy + r * 0.68f, labelPaint)
        canvas.drawText("MÁX: ${maxSpeedKmh.roundToInt()} km/h", cx, cy + r + 35f, valuePaint)
    }

    private fun dibujarRadarG(canvas: Canvas, cx: Float, cy: Float, r: Float, accent: Int) {
        val ringPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.parseColor("#252A3A")
            style = Paint.Style.STROKE
            strokeWidth = 4f
        }
        canvas.drawCircle(cx, cy, r, ringPaint)
        canvas.drawCircle(cx, cy, r * 0.5f, ringPaint)
        canvas.drawLine(cx - r, cy, cx + r, cy, ringPaint)
        canvas.drawLine(cx, cy - r, cx, cy + r, ringPaint)

        // Punto de Fuerza G
        val maxOffset = r * 0.85f
        val dotX = (cx + (gForceX / 1.2f) * maxOffset).coerceIn(cx - maxOffset, cx + maxOffset)
        val dotY = (cy + (gForceY / 1.2f) * maxOffset).coerceIn(cy - maxOffset, cy + maxOffset)

        canvas.drawCircle(dotX, dotY, 13f, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = accent })
        canvas.drawText("G-FORCE", cx, cy - r - 18f, labelPaint)

        val totalG = hypot(gForceX, gForceY)
        canvas.drawText(String.format("PICO: %.2f G", maxGForce), cx, cy + r + 32f, valuePaint)

        // Cronómetro 0-100 km/h
        val chronoText = if (bestZeroToHundredSec > 0f) {
            String.format("0-100: %.1f s", bestZeroToHundredSec)
        } else if (isChronoRunning) {
            val elapsed = (SystemClock.elapsedRealtime() - chronoStartTime) / 1000f
            String.format("0-100: %.1f s...", elapsed)
        } else {
            "0-100: LISTO"
        }
        canvas.drawText(chronoText, cx, cy + r + 66f, labelPaint)
    }

    private fun dibujarTelemetriaDerecha(canvas: Canvas, cx: Float, cy: Float, r: Float, accent: Int) {
        val rect = RectF(cx - r, cy - r, cx + r, cy + r)
        canvas.drawArc(rect, 150f, 240f, false, dialRingPaint.apply { strokeWidth = 14f })

        // Arco dinámico según fuerza G total
        val gRatio = (hypot(gForceX, gForceY) / 1.0f).coerceIn(0f, 1f)
        canvas.drawArc(rect, 150f, gRatio * 240f, false, activeArcPaint.apply { strokeWidth = 14f })

        dialRingPaint.strokeWidth = 22f
        activeArcPaint.strokeWidth = 22f

        canvas.drawText("TELEMETRÍA", cx, cy - r - 18f, labelPaint)
        canvas.drawText("${altitudeMeters.roundToInt()} m", cx, cy - 10f, valuePaint)
        canvas.drawText("ALTITUD GPS", cx, cy + 18f, labelPaint)

        val dirs = arrayOf("N", "NE", "E", "SE", "S", "SO", "O", "NO")
        val dirIndex = (((bearingDegrees + 22.5f) % 360f) / 45f).toInt().coerceIn(0, 7)
        canvas.drawText("RUMBO: ${dirs[dirIndex]} ${bearingDegrees.roundToInt()}°", cx, cy + r + 32f, valuePaint)
        canvas.drawText("TEMA: ${themeNames[themeIndex]}", cx, cy + r + 66f, labelPaint)
    }

    override fun onLocationChanged(location: Location) {
        if (location.hasSpeed()) {
            targetSpeedKmh = location.speed * 3.6f
            if (targetSpeedKmh > maxSpeedKmh) maxSpeedKmh = targetSpeedKmh

            // Lógica automática de 0 a 100 km/h
            if (targetSpeedKmh < 2.0f) {
                isChronoRunning = false
            } else if (!isChronoRunning && targetSpeedKmh >= 2.0f && targetSpeedKmh < 15.0f) {
                isChronoRunning = true
                chronoStartTime = SystemClock.elapsedRealtime()
            } else if (isChronoRunning && targetSpeedKmh >= 100.0f) {
                val timeSec = (SystemClock.elapsedRealtime() - chronoStartTime) / 1000f
                if (bestZeroToHundredSec == 0f || timeSec < bestZeroToHundredSec) {
                    bestZeroToHundredSec = timeSec
                }
                isChronoRunning = false
            }
        }
        if (location.hasAltitude()) altitudeMeters = location.altitude
        if (location.hasBearing()) bearingDegrees = location.bearing
    }

    override fun onSensorChanged(event: SensorEvent?) {
        if (event?.sensor?.type == Sensor.TYPE_ACCELEROMETER) {
            val rawX = event.values[0] / 9.81f
            val rawY = (event.values[2] - 4.0f) / 9.81f
            gForceX = gForceX * 0.85f + rawX * 0.15f
            gForceY = gForceY * 0.85f + rawY * 0.15f

            val currentG = hypot(gForceX, gForceY)
            if (currentG > maxGForce && currentG < 2.5f) {
                maxGForce = currentG
            }
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}

    override fun onGetTemplate(): Template {
        val actionStrip = ActionStrip.Builder()
            .addAction(
                Action.Builder()
                    .setTitle("Color: ${themeNames[themeIndex]}")
                    .setOnClickListener {
                        themeIndex = (themeIndex + 1) % themeColors.size
                        invalidate()
                    }
                    .build()
            )
            .addAction(
                Action.Builder()
                    .setTitle("Reset")
                    .setOnClickListener {
                        maxSpeedKmh = 0f
                        maxGForce = 0f
                        bestZeroToHundredSec = 0f
                    }
                    .build()
            )
            .build()

        return NavigationTemplate.Builder()
            .setActionStrip(actionStrip)
            .build()
    }
}
""",

    ".github/workflows/build_apk.yml": """name: Compilar APK Ibiza Sport HMI

on:
  push:
    branches: [ "main", "master" ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Descargar código
        uses: actions/checkout@v4

      - name: Configurar JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'

      - name: Configurar Gradle 8.7
        uses: gradle/actions/setup-gradle@v4
        with:
          gradle-version: '8.7'

      - name: Compilar APK Lista para Instalar
        run: gradle assembleDebug --no-daemon

      - name: Publicar APK para Descarga
        uses: actions/upload-artifact@v4
        with:
          name: Ibiza-Sport-HMI-APK
          path: app/build/outputs/apk/debug/app-debug.apk
"""
}

for ruta, contenido in archivos.items():
    directorio = os.path.dirname(ruta)
    if directorio:
        os.makedirs(directorio, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(contenido)

print("Proyecto 'Ibiza Sport HMI' generado con exito.")