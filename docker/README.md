services:
  db:
    image: postgres:17
    container_name: rag
    restart: unless-stopped
    env_file: .env
    volumes:
      - db_data:/var/lib/postgresql/data
      - ./init:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"

volumes:
  db_data: