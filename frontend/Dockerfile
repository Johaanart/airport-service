FROM nginxinc/nginx-unprivileged:1.27-alpine

COPY index.html app.js plotly.min.js /usr/share/nginx/html/

# La imagen "unprivileged" escucha en 8080 y no corre como root
EXPOSE 8080
