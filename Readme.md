# Dockerizing Django with Postgres, Gunicorn, and Redis

## Want to use this project?

### Development

Uses the default Django development server.

1. Create virtual environment
2. Install requierements.dev.txt
3. Make migrations and create super user
4. Open another terminal, install dependences tailwind and start tailwind
5. Run Django, has browser reload
6. Once the application is finished, the Tailwind build must be executed

    ```sh
    python3 -m venv .venv
    source .venv/bin/activate

    pip install -r requirements.dev.txt

    python manage.py migrate
    python manage.py createsuperuser

    npm --prefix theme/static_src/ install
    python manage.py tailwind start

    python manage.py runserver

    python manage.py tailwind build

    ```

    Test it out at [http://localhost:8000](http://localhost:8000).

### Production

Uses gunicorn + Redis.

1. Rename an edit *.env.sample* to *.env*. Update the environment variables.
2. Build the images and run the containers:

    ```sh
    scp -P 38 -r chroma_db magoreal@173.212.248.84:/home/magoreal/Django/pliego-es
    scp -P 38 -r media magoreal@173.212.248.84:/home/magoreal/Django/pliego-es
    docker-compose up -d --build
    docker compose exec pliego-django python manage.py collectstatic --settings=config.prod
    docker compose exec pliego-django python manage.py migrate --settings=config.prod
    docker compose exec pliego-django python manage.py createsuperuser --settings=config.prod
    ```

    Test it out at [http://localhost:8003](http://localhost:8003).

cp nginx.conf /etc/nginx/sites-available/pliego.magoreal.com
ln -s /etc/nginx/sites-available/pliego.magoreal.com /etc/nginx/sites-enabled/



tree -I '.venv|__pycache__|*.pyc|db.sqlite3|static|media|node_modules|migrations|__init__.py|theme|examples|chromadb|*.sh|docker*|Dock*'


    path('admin/', admin.site.urls),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path("logout/", LogoutView.as_view(), name="logout"),
    path('pliego/', include('pliego_esp.urls')),
    path('prepare-doc/', include('prep_doc_gen.urls')),
    path('esp-generica/', include('esp_generica.urls')),
    path('embeddings/', include('embeddings.urls'))