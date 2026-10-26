package com.ibiza.sporthmi

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
            "Permiso GPS Activo.\n\nConecta tu celular al SEAT Ibiza y abre 'Ibiza Sport HMI' en la pantalla de Android Auto."
        } else {
            "Se requiere permiso de Ubicación para medir la velocidad por GPS y la altitud en tiempo real."
        }
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        actualizarEstado()
    }
}
