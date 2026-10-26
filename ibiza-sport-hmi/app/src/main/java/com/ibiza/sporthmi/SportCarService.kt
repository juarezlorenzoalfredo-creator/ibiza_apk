package com.ibiza.sporthmi

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
