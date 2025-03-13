FROM python:3.12.9-bookworm
ARG user=1001
ARG home=/home/$user
RUN       pip install arcgis==2.4.0 && \
          pip install Jinja2==3.1.6 && \
          pip install openpyxl==3.1.5
RUN addgroup docker &&  useradd -ms /bin/bash -G docker $user
RUN chmod -R 777 $home
WORKDIR $home
USER $user
COPY --chown=$user . .
CMD ["python","chefs_soils.py"]
