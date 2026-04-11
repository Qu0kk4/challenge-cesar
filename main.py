#!/usr/bin/env python3
from src.agents.coordinator import Coordinator

def main():
    print("🤖 Agente LDAP Auto-Adaptativo - Mercado Libre")
    print("=" * 50)
    
    agent = Coordinator()
    
    while True:
        try:
            query = input("\n❓ Tu consulta (o 'salir'): ").strip()
            if query.lower() in ["salir", "exit", "quit"]:
                break
            
            if not query:
                continue
            
            print("\n⏳ Procesando...")
            response = agent.run(query)
            print(f"\n✅ {response}")
            
        except KeyboardInterrupt:
            print("\n👋 Chau!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
