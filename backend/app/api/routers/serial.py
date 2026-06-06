"""Router para gerenciamento da conexão serial com o ESP32."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.serial_service import serial_gateway

router = APIRouter(prefix="/serial", tags=["serial"])


class ConnectRequest(BaseModel):
    port: str
    robot_id: int
    robot_name: str


@router.get("/ports")
def list_ports():
    return serial_gateway.list_ports()


@router.get("/status")
def get_status():
    s = serial_gateway.status
    return {
        "connected": s.connected,
        "connecting": s.connecting,
        "port": s.port,
        "robot_id": s.robot_id,
        "robot_name": s.robot_name,
        "error": s.error,
    }


@router.post("/connect")
def connect(req: ConnectRequest):
    try:
        serial_gateway.connect(
            port=req.port,
            baud=115200,
            robot_id=req.robot_id,
            robot_name=req.robot_name,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True, "message": f"Conectando à porta {req.port}…"}


@router.post("/disconnect")
def disconnect():
    serial_gateway.disconnect()
    return {"ok": True, "message": "Desconectado."}
