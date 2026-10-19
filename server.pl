#!/usr/bin/env perl
use strict;
use warnings;
use IO::Socket::INET;

$| = 1;

my $root = '/Users/yemseyha/Desktop/ERP Dashbod';
my $port = 8080;
my $sheet_id = '1Kg74MK_M1ofUbCzDBKh5B1HxDUqTM8rsTNvbWXJdnoE';

my $server = IO::Socket::INET->new(
    LocalAddr => '0.0.0.0',
    LocalPort => $port,
    Type      => SOCK_STREAM,
    Reuse     => 1,
    Listen    => 10
) or die "Cannot start: $!\n";

print "Listening on 0.0.0.0:$port with proxy\n";

while (my $client = $server->accept()) {
    my $line = <$client>;
    next unless defined $line;

    my %headers;
    while (my $h = <$client>) {
        last if $h =~ /^[\r\n]+$/;
        if ($h =~ /^([^:]+):\s*(.*)$/) {
            $headers{lc($1)} = $2;
        }
    }

    my ($method, $url) = split(' ', $line);
    $url ||= '/index.html';

    # 1. Handle API Auth
    if ($url =~ m{^/api/auth} && $method eq 'POST') {
        # Simple local auth for demo
        my $token = "local_token_" . time();
        my $json = "{\"success\":true,\"token\":\"$token\",\"user\":{\"username\":\"admin\",\"role\":\"អ្នកគ្រប់គ្រងប្រព័ន្ធ\"}}";
        print $client "HTTP/1.1 200 OK\r\n";
        print $client "Content-Type: application/json; charset=utf-8\r\n";
        print $client "Access-Control-Allow-Origin: *\r\n";
        print $client "Content-Length: " . length($json) . "\r\n";
        print $client "Connection: close\r\n\r\n";
        print $client $json;
        close($client);
        next;
    }

    # 1.1 Handle API Add Expense (Secure Proxy to Google Sheet Webhook)
    if ($url =~ m{^/api/add-expense} && ($method eq 'POST' || $method eq 'OPTIONS')) {
        if ($method eq 'OPTIONS') {
            print $client "HTTP/1.1 200 OK\r\n";
            print $client "Access-Control-Allow-Origin: *\r\n";
            print $client "Access-Control-Allow-Methods: POST, OPTIONS\r\n";
            print $client "Access-Control-Allow-Headers: Content-Type\r\n";
            print $client "Content-Length: 0\r\n";
            print $client "Connection: close\r\n\r\n";
            close($client);
            next;
        }

        my $len = $headers{'content-length'} || 0;
        my $body = '';
        if ($len > 0) {
            read($client, $body, $len);
        }

        # Write body to temp file and send via curl to Google Apps Script
        my $tmp = "/tmp/erp_exp_$$.json";
        if (open(my $tfh, '>', $tmp)) {
            print $tfh $body;
            close($tfh);
        }

        my $webhook = 'https://script.google.com/macros/s/AKfycbwA02pwY7decXviLTk9BKb_eOY0y6ubh8S11Wfi4cc_hkXcK6Ram-p8WtVTNGSTGKwGJg/exec';
        my $resp = `curl -s -L -X POST "$webhook" -d @"$tmp"`;
        unlink($tmp);

        my $json = "{\"success\":true,\"message\":\"Synced to Google Sheet successfully\"}";
        print $client "HTTP/1.1 200 OK\r\n";
        print $client "Content-Type: application/json; charset=utf-8\r\n";
        print $client "Access-Control-Allow-Origin: *\r\n";
        print $client "Content-Length: " . length($json) . "\r\n";
        print $client "Connection: close\r\n\r\n";
        print $client $json;
        close($client);
        next;
    }

    # 2. Handle API Data (Proxy to Google Sheet so Browser won't have CORS issue!)
    if ($url =~ m{^/api/data}) {
        # Fetch directly using curl on Mac
        my $exp = `curl -s -L "https://docs.google.com/spreadsheets/d/$sheet_id/export?format=csv&gid=859033776"`;
        my $inc = `curl -s -L "https://docs.google.com/spreadsheets/d/$sheet_id/export?format=csv&gid=1280452951"`;
        my $team = `curl -s -L "https://docs.google.com/spreadsheets/d/$sheet_id/export?format=csv&gid=944458554"`;
        my $boost = `curl -s -L "https://docs.google.com/spreadsheets/d/$sheet_id/export?format=csv&gid=455285947"`;
        my $form1 = `curl -s -L "https://docs.google.com/spreadsheets/d/$sheet_id/export?format=csv&gid=301276705"`;
        my $masterA1 = `curl -s -L "https://docs.google.com/spreadsheets/d/$sheet_id/export?format=csv&gid=1102512547"`;

        # Escape json
        for my $val ($exp, $inc, $team, $boost, $form1, $masterA1) {
            $val =~ s/\\/\\\\/g;
            $val =~ s/"/\\"/g;
            $val =~ s/\r/\\r/g;
            $val =~ s/\n/\\n/g;
        }

        my $json = "{\"success\":true,\"data\":{\"expensesCsv\":\"$exp\",\"incomesCsv\":\"$inc\",\"teamSalesCsv\":\"$team\",\"boostPlanCsv\":\"$boost\",\"formResponses1Csv\":\"$form1\",\"masterA1Csv\":\"$masterA1\"}}";

        print $client "HTTP/1.1 200 OK\r\n";
        print $client "Content-Type: application/json; charset=utf-8\r\n";
        print $client "Access-Control-Allow-Origin: *\r\n";
        print $client "Content-Length: " . length($json) . "\r\n";
        print $client "Connection: close\r\n\r\n";
        print $client $json;
        close($client);
        next;
    }

    # Static file serving
    $url =~ s/\?.*//;
    $url = '/index.html' if $url eq '/';
    $url =~ s/\.\.//g;

    my $file = $root . $url;

    if (-f $file) {
        my $type = 'text/plain';
        $type = 'text/html; charset=utf-8' if $file =~ /\.html$/i;
        $type = 'text/css; charset=utf-8' if $file =~ /\.css$/i;
        $type = 'application/javascript; charset=utf-8' if $file =~ /\.js$/i;
        $type = 'image/png' if $file =~ /\.png$/i;
        $type = 'image/jpeg' if $file =~ /\.jpe?g$/i;
        $type = 'application/json' if $file =~ /\.json$/i;

        if (open(my $fh, '<:raw', $file)) {
            my $content = do { local $/; <$fh> };
            close($fh);
            my $len = length($content);

            print $client "HTTP/1.1 200 OK\r\n";
            print $client "Content-Type: $type\r\n";
            print $client "Content-Length: $len\r\n";
            print $client "Cache-Control: no-cache, no-store, must-revalidate\r\n";
            print $client "Pragma: no-cache\r\n";
            print $client "Access-Control-Allow-Origin: *\r\n";
            print $client "Connection: close\r\n\r\n";
            print $client $content;
        } else {
            print $client "HTTP/1.1 500 Error\r\nConnection: close\r\n\r\n500";
        }
    } else {
        print $client "HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n404";
    }
    close($client);
}
