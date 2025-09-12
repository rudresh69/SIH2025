# TRINETRA - Geological Event Monitoring System

A comprehensive geological event monitoring system that provides real-time sensor data visualization and risk assessment for rockfall, rainfall, and landslide prevention.

## Project Structure

```
├── .gitignore
├── backend/
│   ├── main.py                # FastAPI backend server
│   ├── requirements.txt       # Python dependencies
│   └── sensors/              # Sensor simulation modules
│       ├── __init__.py
│       ├── displacement.py   # Crack, inclinometer, extensometer sensors
│       ├── environmental.py  # Rain sensor
│       ├── hydro.py          # Moisture and piezometer sensors
│       └── sesmic.py         # Accelerometer, geophone, seismometer sensors
└── frontend/
    ├── public/               # Static assets
    ├── src/
    │   ├── app/              # Next.js app router pages
    │   ├── components/       # React components
    │   │   ├── ui/           # UI components (shadcn/ui)
    │   │   └── mine-safety-dashboard.tsx  # Main dashboard component
    │   ├── hooks/            # Custom React hooks
    │   ├── lib/              # Utility functions
    │   └── visual-edits/     # Visual editing tools
    ├── package.json          # Frontend dependencies
    └── tsconfig.json         # TypeScript configuration
```

## Technology Stack

### Backend
- **FastAPI**: High-performance Python web framework for building APIs
- **Uvicorn**: ASGI server for running the FastAPI application
- **Python-multipart**: For handling form data

### Frontend
- **Next.js 15**: React framework with app router
- **React 19**: UI library
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: Reusable UI components built with Radix UI and Tailwind
- **Recharts**: Charting library for data visualization
- **Sonner**: Toast notifications

## Features

### Backend Services

The backend provides simulated sensor data through several endpoints:

1. **Seismic Sensors** (`/sensor/sesmic`)
   - Accelerometer: Measures ground acceleration
   - Geophone: Detects ground vibrations
   - Seismometer: Measures seismic waves

2. **Displacement Sensors** (`/sensor/displacement`)
   - Crack Sensor: Monitors crack formation and growth
   - Inclinometer: Measures slope angles
   - Extensometer: Measures deformation

3. **Hydrological Sensors** (`/sensor/hydro`)
   - Moisture Sensor: Measures soil moisture content
   - Piezometer: Measures groundwater pressure

4. **Environmental Sensors** (`/sensor/environment`)
   - Rain Sensor: Measures precipitation

5. **Risk Assessment** (`/risk-level`)
   - Analyzes data from multiple sensors
   - Provides risk level classification (LOW, MEDIUM, HIGH)

### Frontend Dashboard

The mine safety dashboard provides a comprehensive interface for monitoring:

- Real-time sensor readings with historical trends
- Risk level indicators and alerts
- Sensor selection and filtering
- Alert acknowledgment system
- Data visualization with charts and graphs

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 18+

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

The backend API will be available at http://localhost:8000

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend application will be available at http://localhost:3001

## API Documentation

Once the backend is running, you can access the auto-generated API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Purpose

This system is designed to help geological monitoring operations prevent hazardous events by:

1. Continuously monitoring critical parameters across multiple sensor types
2. Providing early warning of potential geological hazards (rockfall, rainfall, landslides)
3. Visualizing trends to identify developing issues
4. Offering risk assessment based on multiple sensor inputs
5. Supporting three distinct event types with specialized monitoring protocols

The combination of various sensor types allows for comprehensive monitoring of conditions that may lead to geological events, enabling proactive safety measures and timely evacuation protocols.