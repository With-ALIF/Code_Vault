#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#define max 1024


char *trim(char *s) {
    while (*s == ' ' || *s == '\t') 
        s++;
    char *end = s + strlen(s) - 1;
    while (end >= s && (*end == ' ' || *end == '\t' || *end == '\n' || *end == ';')) {  
        *end = '\0';
        end--;    
    }
    return s;
}


int get_index(char headers[][50], int n, char *field) {
    for (int i = 0; i < n; i++) {
        if (strcmp(headers[i], field) == 0)
            return i;
    }
    return -1;
}

int main() {
    char query[max];
    printf("Enter Query: \n");
    fgets(query, max, stdin);


    char *from = strstr(query, "FROM");
    if (!from) {
        printf("Error: Missing FROM.\n");
        return 0;
    }


    char selectPart[200];
    strncpy(selectPart, query + 6, from - (query + 6)); // skip "SELECT "
    selectPart[from - (query + 6)] = '\0';
    strcpy(selectPart, trim(selectPart));


    char *where = strstr(query, "WHERE");
    char table[50];
    if (where) {
        strncpy(table, from + 4, where - (from + 4));
        table[where - (from + 4)] = '\0';
    } else {
        strcpy(table, from + 4);
    }
    strcpy(table, trim(table)); 


    char condField[50] = "", condValue[50] = "";
    if (where) {
        sscanf(where + 5, "%[^=]=%s", condField, condValue); // skip "WHERE "
        strcpy(condField, trim(condField));
        strcpy(condValue, trim(condValue));
    }


    char filename[60];
    sprintf(filename, "%s.txt", table);
    FILE *fp = fopen(filename, "r");
    if (!fp) {
        printf("Error: Table '%s' not found.\n", table);
        return 0;
    }


    char line[max];
    fgets(line, max, fp);
    char headers[50][50];
    int hcount = 0;
    char *tok = strtok(line, ",\n");
    while (tok) {
        strcpy(headers[hcount++], trim(tok));
        tok = strtok(NULL, ",\n");
    }


    char fields[50][50];
    int fcount = 0, all = 0;
    if (strcmp(selectPart, "*") == 0) {
        all = 1;
        fcount = hcount;
        for (int i = 0; i < hcount; i++)
            strcpy(fields[i], headers[i]);
    } else {
        tok = strtok(selectPart, ",");
        while (tok) {
            strcpy(fields[fcount++], trim(tok));
            tok = strtok(NULL, ",");
        }

        for (int i = 0; i < fcount; i++) {
            if (get_index(headers, hcount, fields[i]) == -1) {
                printf("Error: Field '%s' not found in table '%s'.\n", fields[i], table);
                return 0;
            }
        }
    }


    int condIndex = -1;
    if (strlen(condField) > 0) {
        condIndex = get_index(headers, hcount, condField);
        if (condIndex == -1) {
            printf("Error: Field '%s' not found in table '%s'.\n", condField, table);
            return 0;
        }
    }


    printf("Query Parsed Successfully!\nResults:\n");
    for (int i = 0; i < fcount; i++)
        printf("%s\t", fields[i]);
    printf("\n");


    while (fgets(line, max, fp)) {
        char cols[50][50];
        int c = 0;
        tok = strtok(line, ",");
        while (tok) {
            strcpy(cols[c++], trim(tok));
            tok = strtok(NULL, ",");
        }

        if(c != hcount)
            continue;


        if (condIndex != -1 && strcmp(cols[condIndex], condValue) != 0)
            continue;


        for (int i = 0; i < fcount; i++) {
            int idx = get_index(headers, hcount, fields[i]);
            printf("%s\t", cols[idx]);
        }
        printf("\n");
    }

    fclose(fp);
    return 0;    
}
