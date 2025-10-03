#!/usr/bin/env python3
"""
Script para inicializar y gestionar la base de datos.
Uso: python init_db.py [reset|create|check]
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from infra.database import initialize_database, create_tables, drop_tables, reset_database, check_database_health

def main():
    """Función principal del script"""
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
    else:
        command = 'create'
    
    print("🚀 Inicializando gestión de base de datos...")
    print("=" * 50)
    
    try:
        # Inicializar conexión
        initialize_database()
        
        if command == 'reset':
            print("⚠️ RESETEAR BASE DE DATOS")
            confirm = input("¿Estás seguro? Esto eliminará todos los datos (y/n): ")
            if confirm.lower() == 'y':
                reset_database()
            else:
                print("❌ Operación cancelada")
                return
                
        elif command == 'create':
            print("📊 Creando tablas de base de datos...")
            create_tables()
            
        elif command == 'drop':
            print("⚠️ ELIMINAR TODAS LAS TABLAS")
            confirm = input("¿Estás seguro? Esto eliminará todos los datos (y/n): ")
            if confirm.lower() == 'y':
                drop_tables()
            else:
                print("❌ Operación cancelada")
                return
                
        elif command == 'check':
            print("🔍 Verificando estado de la base de datos...")
            if check_database_health():
                print("✅ Base de datos funcionando correctamente")
            else:
                print("❌ Problemas con la base de datos")
                return
                
        else:
            print(f"❌ Comando desconocido: {command}")
            print("Comandos disponibles: reset, create, drop, check")
            return
            
        print("✅ Operación completada exitosamente")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()