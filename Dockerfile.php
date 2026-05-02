FROM php:8.2-apache

# Install Python and dependencies
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*
RUN pip3 install mysql-connector-python pymongo --break-system-packages

# Install PDO MySQL and mysqli extensions (required for db.php)
RUN docker-php-ext-install pdo pdo_mysql mysqli

# Enable Apache mod_rewrite (useful for clean URLs)
RUN a2enmod rewrite
