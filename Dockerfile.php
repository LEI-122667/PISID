FROM php:8.2-apache

# Install PDO MySQL and mysqli extensions (required for db.php)
RUN docker-php-ext-install pdo pdo_mysql mysqli

# Enable Apache mod_rewrite (useful for clean URLs)
RUN a2enmod rewrite
