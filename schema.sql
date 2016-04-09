drop table if exists users;

create table users (
       id integer primary key autoincrement,
       first_name varchar,
       surname varchar,
       username varchar unique,
       password varchar,
       email varchar unique,
       show_all_services boolean default true
       );

-- Table where is saved the services enables to be shown in the services page.
create table services_page_services_enabled (
      service_id varchar,
      user_id    integer,
      shown boolean default true,
      custom_name varchar default null,
      primary key (service_id,user_id),
      foreign key (user_id) references users(id) on delete cascade
      );

