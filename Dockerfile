FROM php:7.4-apache
RUN apt update && apt -y install libfreetype6-dev  libjpeg62-turbo-dev zlib1g-dev libpng-dev \
 && docker-php-ext-configure gd --with-freetype --with-jpeg \
 && docker-php-ext-install -j$(nproc) gd mysqli
RUN apt -y install git
RUN git clone https://github.com/gnuboard/gnuboard5.git /var/www/html/                                                                                                                                                                                                         
