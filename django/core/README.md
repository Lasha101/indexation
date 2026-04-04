Django Fundamentals: Minimalist Web App

A minimalist, highly accessible Django web application designed as an educational tool to introduce students to the core concepts of the Django framework.

This project strips away complex boilerplate to clearly demonstrate the fundamental flow of a Django application: from routing and views to the ORM and template rendering. It serves as a perfect starting point for understanding how Python, HTML, and databases interact within the Model-View-Template (MVT) architecture.

Features & Concepts Demonstrated

Django MVT Architecture: Clear separation of Models, Views, and Templates.

Database Integration: Utilizing Django's Object-Relational Mapper (ORM) with a lightweight SQLite database.

Form Handling & Security: Processing POST requests and securing forms using Django's built-in {% csrf_token %}.

Dynamic Rendering: Passing context dictionaries from Python views to render dynamic content in HTML templates.

Routing: Basic URL configuration and path mapping.

Technologies Used

Backend: Python, Django

Database: SQLite (Default)

Frontend: HTML5, Django Template Language (DTL)

Project Structure Highlight

models.py: Defines the Person database schema.

views.py: Contains the index logic to handle POST requests, create database entries, and pass context.

urls.py: Maps the root URL to the index view.

index.html: The frontend template featuring a user input form and a dynamic greeting.


